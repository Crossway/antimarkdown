# -*- coding: utf-8 -*-
"""antimarkdown.nodes -- text nodes and their rendering behavior.

Node classes match up to HTML elements, and should be named after the
corresponding tag in all upper-case. Nodes should produce inner text
(including children) and tail text (not siblings).
"""
import re
import collections

hex_color = collections.defaultdict(lambda: 'none')
try:
    import mdx_hilite
    hex_color.update((h, c) for c, h in mdx_hilite.color_hex.iteritems())
except ImportError:
    pass


def escape(text, characters):
    for c in characters:
        text = text.replace(c, ur'\%s' % c)
    return text


def escape_re(text, *regexps):
    for r in regexps:
        text = r.sub(ur'\\\1', text)
    return text


def eltext(text, escape_text=True):
    if text is None:
        text = u''

    if escape_text:
        return escape(text, u'`')
    else:
        return text


WHITESPACE_CP = re.compile(ur'\s+')


def whitespace(text):
    return WHITESPACE_CP.sub(u' ', text.replace(u'\n', u' '))


NEWLINES_CP = re.compile(u'\n\n+', re.MULTILINE)


def newlines(text):
    return NEWLINES_CP.sub(u'\n\n', text)


NORMALIZE_NEWLINES_CP = re.compile(ur'\n\n+(?![^\n]+\n[-=]|#)', re.MULTILINE)


def normalize(markdown_text):
    norm = markdown_text
    norm = NORMALIZE_NEWLINES_CP.sub(u'\n\n', norm)
    return u'\n'.join(n.rstrip() for n in norm.splitlines())


class Root(collections.deque):
    def __unicode__(self):
        return normalize(u''.join(unicode(node) for node in self))


class Node(collections.deque):
    def __init__(self, parent, el, blackboard, *args, **kwargs):
        super(Node, self).__init__(*args, **kwargs)
        self.parent = parent
        parent.append(self)
        self.el = el
        self.tag = self.__class__.__name__.lower()
        self.blackboard = blackboard

    def __unicode__(self):
        self.blackboard.setdefault('env', []).append(self.tag)
        text = self.text()
        tail = self.tail()
        self.blackboard['env'].pop()

        return text + tail

    def text(self):
        return u'%s%s' % (
            whitespace(eltext(self.el.text)).lstrip(),
            u''.join(unicode(node) for node in self),
        )

    def tail(self):
        tail = eltext(self.el.tail)
        if tail:
            return whitespace(tail)
        else:
            return tail


class Block(Node):
    def tail(self):
        return u'\n\n' + whitespace(eltext(self.el.tail)).lstrip()


class BlockWithSpacing(Block):
    def __unicode__(self):
        li_env = self.blackboard.get('li-nested-block')
        if li_env:
            li_env[-1] = True
        return super(Block, self).__unicode__()


class P(BlockWithSpacing):
    def text(self):
        if self.blackboard.get('li-nested-block'):
            spacer = u'\n\n'
        else:
            spacer = u''
        return spacer + super(P, self).text()


INNER_SQ_LBRACKET_ESCAPE_CP = re.compile(ur'((?<!!)\[)')
INNER_SQ_RBRACKET_ESCAPE_CP = re.compile(ur'(\](?!\())')


class A(Node):
    def text(self):
        el = self.el
        href = el.attrib.get('href')
        if href and href.startswith(u'mailto:'):
            href = href[7:]
        if href == el.text:
            return u'<%s>' % href
        else:
            return u"[%(text)s](%(href)s%(title)s)" % {
                'text': escape_re(super(A, self).text(),
                                  INNER_SQ_LBRACKET_ESCAPE_CP,
                                  INNER_SQ_RBRACKET_ESCAPE_CP).rstrip(),
                'title': (u' "%s"' % escape(el.attrib['title'], u'()')) if 'title' in el.attrib else u'',
                'href': (u'<%s>' % escape(el.attrib.get('href'), u'()')) if href else u''
            }


class PRE(BlockWithSpacing):
    def text(self):
        self.blackboard['pre'] = True

        text = u'%s%s' % (
            eltext(self.el.text, escape_text=False),
            u''.join(unicode(node) for node in self),
        )

        result = u'\n'.join(u'    %s' % n for n in text.splitlines())

        del self.blackboard['pre']
        return result


class BLOCKQUOTE(BlockWithSpacing):
    NORMALIZE_BLOCKQUOTES_LEADING_CP = re.compile(ur'(^[^>]*\n)(?: *> *\n)+', re.MULTILINE)
    NORMALIZE_BLOCKQUOTES_TRAILING_CP = re.compile(ur'^(?: *> +\n)+(?! *>)', re.MULTILINE)

    def text(self):
        text = super(BLOCKQUOTE, self).text().rstrip()
        lines = [u'> %s' % n for n in text.splitlines()]
        if lines and lines[0].strip() == u'>':
            lines[0] = u''
        if lines and lines[-1].strip() == u'>':
            lines[-1] = u''
        text = u'\n'.join(lines)
        text = self.NORMALIZE_BLOCKQUOTES_LEADING_CP.sub(ur'\1', text)
        text = self.NORMALIZE_BLOCKQUOTES_TRAILING_CP.sub(u'\n', text)
        text = text or u'>'  # Just in case it's an empty blockquote...
        return text.rstrip()


class ListBlock(Block):
    def tail(self):
        if len(self.blackboard['env']) > 1:
            return whitespace(eltext(self.el.tail)).lstrip()
        else:
            return super(ListBlock, self).tail()


class OL(ListBlock):
    def text(self):
        def numbers():
            i = 0
            while True:
                i += 1
                si = u'%s.' % i
                yield si + (u' ' * max(4 - len(si), 0))
        self.blackboard.setdefault('li-style', []).append(numbers())
        result = newlines(super(OL, self).text())
        self.blackboard['li-style'].pop()
        return result


class UL(ListBlock):
    def text(self):
        self.blackboard.setdefault('li-style', []).append(u'*   ')
        result = newlines(super(UL, self).text())
        self.blackboard['li-style'].pop()
        return result


class LI(Block):
    def text(self):
        li_env = self.blackboard.setdefault('li-nested-block', [])
        li_env.append(False)
        li = self.blackboard.get('li-style', [u'*   '])[-1]
        if hasattr(li, 'next'):
            li = li.next()
        text = whitespace(eltext(self.el.text)).lstrip()

        lines = newlines(u''.join(u'\n' + unicode(node)
                                  if isinstance(node, Block) else unicode(node)
                                  for node in self)
                         ).splitlines()

        if lines:
            space = u' ' * len(li)
            lines[1:] = [u'%s%s' % (space, ln) for ln in lines[1:]]

        lines = u'\n'.join(lines)
        if not text:
            lines = lines.lstrip()

        if li_env[-1] and isinstance(self[0], BlockWithSpacing):
            spacer = u'\n\n'
        else:
            spacer = u''

        return spacer + newlines(li + text + lines)

    def tail(self):
        nested_block = self.blackboard.setdefault('li-nested-block', [False]).pop()
        if nested_block:
            spacer = u'\n\n'
        else:
            spacer = u'\n'

        return spacer + whitespace(eltext(self.el.tail)).lstrip()


class CODE(Node):
    def text(self):
        text = u'%s%s' % (
            eltext(self.el.text, escape_text=False),
            u''.join(unicode(node) for node in self),
        )
        if self.blackboard.get('pre'):
            return text
        else:
            if u'`' in text:
                return u'`` %s ``' % text
            else:
                return u'`%s`' % text


class STRONG(Node):
    def text(self):
        return u'**%s**' % super(STRONG, self).text()

B = STRONG


class EM(Node):
    def text(self):
        return u'*%s*' % super(EM, self).text()

I = EM


class U(Node):
    def text(self):
        return u'<u>%s</u>' % super(U, self).text()


background_color_cp = re.compile(r'background-color\s*:\s*(#[a-f0-9]+);')


class SPAN(Node):
    def text(self):
        match = background_color_cp.findall(self.el.attrib.get('style', ''))
        hex_value = match[0] if match else None
        if hex_value is None:
            return super(SPAN, self).text()
        else:
            return u'%%[%(text)s](%(hex)s)' % {
                'text': super(SPAN, self).text(),
                'hex': hex_color[hex_value],
            }


class IMG(Node):
    def text(self):
        el = self.el
        title = el.attrib.get('title')
        return u'![%(alt)s](<%(src)s>%(title)s)%(text)s' % {
            'alt': escape(el.attrib.get('alt', u''), u'[]'),
            'src': escape(el.attrib.get('src', u''), u'()'),
            'title': u' "%s"' % escape(title, u'"') if title else u'',
            'text': super(IMG, self).text()}

    def tail(self):
        return super(IMG, self).tail() or u' '


class HR(Block):
    def text(self):
        return u'---'


class DIV(Block):
    def text(self):
        return u'<div>%s%s</div>' % (
            (eltext(self.el.text)),
            u''.join(unicode(node) for node in self),
        )

    def tail(self):
        return eltext(self.el.tail)


class Header(Block):
    def tail(self):
        in_li = self.blackboard.get('li-nested-block')
        if in_li:
            spacer = u''
        else:
            spacer = u'\n'
        return spacer + eltext(self.el.tail)


class H1(Header):
    def text(self):
        text = super(H1, self).text()
        if len(self.blackboard['env']) > 1:
            return '\n# %s #' % text
        else:
            return u'\n%s\n%s' % (text, len(text) * '=')


class H2(Header):
    def text(self):
        text = super(H2, self).text()
        if len(self.blackboard['env']) > 1:
            return '\n## %s ##' % text
        else:
            return u'\n%s\n%s' % (text, len(text) * '-')


class H3(Header):
    def text(self):
        return u'\n### %s ###' % super(H3, self).text()


class H4(Header):
    def text(self):
        return u'\n### %s ###' % super(H4, self).text()


class H5(Header):
    def text(self):
        return u'\n##### %s #####' % super(H5, self).text()


class H6(Header):
    def text(self):
        return u'\n###### %s ######' % super(H6, self).text()
