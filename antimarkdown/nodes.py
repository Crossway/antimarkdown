# -*- coding: utf-8 -*-
"""antimarkdown.nodes -- text nodes and their rendering behavior.

Node classes match up to HTML elements, and should be named after the
corresponding tag in all upper-case. Nodes should produce inner text
(including children) and tail text (not siblings).
"""
import collections
import inspect
import re


def escape(text, characters):
    for c in characters:
        text = text.replace(c, r'\%s' % c)
    return text


def escape_re(text, *regexps):
    for r in regexps:
        text = r.sub(r'\\\1', text)
    return text


def eltext(text, escape_text=True):
    if text is None:
        text = ''

    if escape_text:
        return escape(text, '`')
    else:
        return text


WHITESPACE_CP = re.compile(r'\s+')


def whitespace(text):
    return WHITESPACE_CP.sub(' ', text.replace('\n', ' '))


NEWLINES_CP = re.compile('\n\n+', re.MULTILINE)


def newlines(text):
    return NEWLINES_CP.sub('\n\n', text)


NORMALIZE_NEWLINES_CP = re.compile(r'\n\n+(?![^\n]+\n[-=]|#)', re.MULTILINE)


def normalize(markdown_text):
    norm = markdown_text
    norm = NORMALIZE_NEWLINES_CP.sub('\n\n', norm)
    return '\n'.join(n.rstrip() for n in norm.splitlines())


class Root(collections.deque):
    def __str__(self):
        return normalize(''.join(str(node) for node in self))


class Node(collections.deque):
    def __init__(self, parent, el, blackboard, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        parent.append(self)
        self.el = el
        self.tag = self.__class__.__name__.lower()
        self.blackboard = blackboard

    def __str__(self):
        self.blackboard.setdefault('env', []).append(self.tag)
        text = self.text()
        tail = self.tail()
        self.blackboard['env'].pop()

        return text + tail

    def text(self):
        return '%s%s' % (
            whitespace(eltext(self.el.text)).lstrip(),
            ''.join(str(node) for node in self),
        )

    def tail(self):
        tail = eltext(self.el.tail)
        if tail:
            return whitespace(tail)
        else:
            return tail


class Block(Node):
    def tail(self):
        return '\n\n' + whitespace(eltext(self.el.tail)).lstrip()


class BlockWithSpacing(Block):
    def __str__(self):
        li_env = self.blackboard.get('li-nested-block')
        if li_env:
            li_env[-1] = True
        return super().__str__()


class P(BlockWithSpacing):
    def text(self):
        if self.blackboard.get('li-nested-block'):
            spacer = '\n\n'
        else:
            spacer = ''
        return spacer + super().text()


INNER_SQ_LBRACKET_ESCAPE_CP = re.compile(r'((?<!!)\[)')
INNER_SQ_RBRACKET_ESCAPE_CP = re.compile(r'(\](?!\())')


class A(Node):
    def text(self):
        el = self.el
        href = el.attrib.get('href')
        if href and href.startswith('mailto:'):
            href = href[7:]
        if href == el.text:
            return '<%s>' % href
        else:
            return "[%(text)s](%(href)s%(title)s)" % {
                'text': escape_re(super().text(),
                                  INNER_SQ_LBRACKET_ESCAPE_CP,
                                  INNER_SQ_RBRACKET_ESCAPE_CP).rstrip(),
                'title': (' "%s"' % escape(el.attrib['title'], '()')) if 'title' in el.attrib else '',
                'href': ('<%s>' % escape(el.attrib.get('href'), '()')) if href else ''
            }


class PRE(BlockWithSpacing):
    def text(self):
        self.blackboard['pre'] = True

        text = '%s%s' % (
            eltext(self.el.text, escape_text=False),
            ''.join(str(node) for node in self),
        )

        result = '\n'.join('    %s' % n for n in text.splitlines())

        del self.blackboard['pre']
        return result


class BLOCKQUOTE(BlockWithSpacing):
    NORMALIZE_BLOCKQUOTES_LEADING_CP = re.compile(r'(^[^>]*\n)(?: *> *\n)+', re.MULTILINE)
    NORMALIZE_BLOCKQUOTES_TRAILING_CP = re.compile(r'^(?: *> +\n)+(?! *>)', re.MULTILINE)

    def text(self):
        text = super().text().rstrip()
        lines = ['> %s' % n for n in text.splitlines()]
        if lines and lines[0].strip() == '>':
            lines[0] = ''
        if lines and lines[-1].strip() == '>':
            lines[-1] = ''
        text = '\n'.join(lines)
        text = self.NORMALIZE_BLOCKQUOTES_LEADING_CP.sub(r'\1', text)
        text = self.NORMALIZE_BLOCKQUOTES_TRAILING_CP.sub('\n', text)
        text = text or '>'  # Just in case it's an empty blockquote...
        return text.rstrip()


class ListBlock(Block):
    def tail(self):
        if len(self.blackboard['env']) > 1:
            return whitespace(eltext(self.el.tail)).lstrip()
        else:
            return super().tail()


class OL(ListBlock):
    def text(self):
        def numbers():
            i = 0
            while True:
                i += 1
                si = '%s.' % i
                yield si + (' ' * max(4 - len(si), 0))
        self.blackboard.setdefault('li-style', []).append(numbers())
        result = newlines(super().text())
        self.blackboard['li-style'].pop()
        return result


class UL(ListBlock):
    def text(self):
        self.blackboard.setdefault('li-style', []).append('*   ')
        result = newlines(super().text())
        self.blackboard['li-style'].pop()
        return result


class LI(Block):
    def text(self):
        li_env = self.blackboard.setdefault('li-nested-block', [])
        li_env.append(False)
        li = self.blackboard.get('li-style', ['*   '])[-1]
        if inspect.isgenerator(li):
            li = next(li)
        text = whitespace(eltext(self.el.text)).lstrip()

        lines = newlines(''.join('\n' + str(node)
                                 if isinstance(node, Block) else str(node)
                                 for node in self)
                         ).splitlines()

        if lines:
            space = ' ' * len(li)
            lines[1:] = ['%s%s' % (space, ln) for ln in lines[1:]]

        lines = '\n'.join(lines)
        if not text:
            lines = lines.lstrip()

        if li_env[-1] and isinstance(self[0], BlockWithSpacing):
            spacer = '\n\n'
        else:
            spacer = ''

        return spacer + newlines(li + text + lines)

    def tail(self):
        nested_block = self.blackboard.setdefault('li-nested-block', [False]).pop()
        if nested_block:
            spacer = '\n\n'
        else:
            spacer = '\n'

        return spacer + whitespace(eltext(self.el.tail)).lstrip()


class CODE(Node):
    def text(self):
        text = '%s%s' % (
            eltext(self.el.text, escape_text=False),
            ''.join(str(node) for node in self),
        )
        if self.blackboard.get('pre'):
            return text
        else:
            if '`' in text:
                return '`` %s ``' % text
            else:
                return '`%s`' % text


class STRONG(Node):
    def text(self):
        return '**%s**' % super().text()

B = STRONG


class EM(Node):
    def text(self):
        return '*%s*' % super().text()

I = EM


class U(Node):
    def text(self):
        return '<u>%s</u>' % super().text()


background_color_cp = re.compile(r'background-color\s*:\s*(#[a-f0-9]+);')


class SPAN(Node):
    pass


class IMG(Node):
    def text(self):
        el = self.el
        title = el.attrib.get('title')
        return '![%(alt)s](<%(src)s>%(title)s)%(text)s' % {
            'alt': escape(el.attrib.get('alt', ''), '[]'),
            'src': escape(el.attrib.get('src', ''), '()'),
            'title': ' "%s"' % escape(title, '"') if title else '',
            'text': super().text()}

    def tail(self):
        return super().tail() or ' '


class HR(Block):
    def text(self):
        return '---'


class DIV(Block):
    def text(self):
        return '<div>%s%s</div>' % (
            (eltext(self.el.text)),
            ''.join(str(node) for node in self),
        )

    def tail(self):
        return eltext(self.el.tail)


class Header(Block):
    def tail(self):
        in_li = self.blackboard.get('li-nested-block')
        if in_li:
            spacer = ''
        else:
            spacer = '\n'
        return spacer + eltext(self.el.tail)


class H1(Header):
    def text(self):
        text = super().text()
        if len(self.blackboard['env']) > 1:
            return '\n# %s #' % text
        else:
            return '\n%s\n%s' % (text, len(text) * '=')


class H2(Header):
    def text(self):
        text = super().text()
        if len(self.blackboard['env']) > 1:
            return '\n## %s ##' % text
        else:
            return '\n%s\n%s' % (text, len(text) * '-')


class H3(Header):
    def text(self):
        return '\n### %s ###' % super(H3, self).text()


class H4(Header):
    def text(self):
        return '\n### %s ###' % super().text()


class H5(Header):
    def text(self):
        return '\n##### %s #####' % super().text()


class H6(Header):
    def text(self):
        return '\n###### %s ######' % super().text()
