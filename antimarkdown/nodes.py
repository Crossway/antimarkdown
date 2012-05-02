# -*- coding: utf-8 -*-
"""antimarkdown.nodes -- text nodes and their rendering behavior.

Node classes match up to HTML elements, and should be named after the
corresponding tag in all upper-case. Nodes should produce inner text
(including children) and tail text (not siblings).
"""
import re
import collections


def escape(text, characters):
    for c in characters:
        text = text.replace(c, ur'\%s' % c)
    return text


WHITESPACE_CP = re.compile(r'\s+')


def whitespace(text):
    return WHITESPACE_CP.sub(u' ', text.replace(u'\n', u' '))


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
        return (self.text() or u'') + (self.tail() or u'')

    def text(self):
        return u'%s%s' % (
            whitespace(self.el.text or u'').lstrip(),
            u''.join(unicode(node) for node in self),
            )

    def tail(self):
        tail = self.el.tail or u''
        if tail:
            return whitespace(tail)
        else:
            return tail


class Block(Node):
    def tail(self):
        return (self.el.tail or u'').rstrip() + u'\n\n'


class P(Block):
    pass


class A(Node):
    def text(self):
        el = self.el
        href = el.attrib.get('href')
        if href == el.text:
            return u'<%s>' % href
        else:
            return u"[%(text)s](%(href)s%(title)s)" % {
                'text': escape(super(A, self).text(), u'[]'),
                'title': (u' "%s"' % escape(el.attrib['title'], u'()')) if 'title' in el.attrib else u'',
                'href': (u'<%s>' % escape(el.attrib.get('href'), u'()')) if href else u''
                }


class PRE(Block):
    def text(self):
        self.blackboard['pre'] = True

        text = u'%s%s' % (
            self.el.text or u'',
            u''.join(unicode(node) for node in self),
            )

        result = u'\n'.join(u'    %s' % n for n in text.splitlines())

        del self.blackboard['pre']
        return result


class BLOCKQUOTE(Block):
    NORMALIZE_BLOCKQUOTES_LEADING_CP = re.compile(ur'(^[^>]*\n)(?: *> *\n)+', re.MULTILINE)
    NORMALIZE_BLOCKQUOTES_TRAILING_CP = re.compile(ur'^(?: *> +\n)+(?! *>)', re.MULTILINE)
    
    def text(self):
        text = super(BLOCKQUOTE, self).text().rstrip()
        lines = [u'> %s' % n for n in text.splitlines()]
        if lines[0].strip() == u'>':
            lines[0] = u''
        if lines[-1].strip() == u'>':
            lines[-1] = u''
        text = u'\n'.join(lines)
        text = self.NORMALIZE_BLOCKQUOTES_LEADING_CP.sub(ur'\1', text)
        text = self.NORMALIZE_BLOCKQUOTES_TRAILING_CP.sub(u'\n', text)
        
        return text.rstrip()

    def tail(self):
        return super(BLOCKQUOTE, self).tail().rstrip() + u'\n\n'


class OL(Block):
    def text(self):
        self.blackboard.setdefault('li-style', []).append(u'1. ')
        return super(OL, self).text().rstrip()


class UL(Block):
    def text(self):
        self.blackboard.setdefault('li-style', []).append(u'* ')
        return super(UL, self).text().rstrip()


class LI(Block):
    def text(self):
        li = self.blackboard.get('li-style', [u'* '])[0]

        text = li + whitespace(self.el.text or u'').lstrip()

        lines = u''.join(u'\n' + unicode(node) if isinstance(node, Block) else unicode(node)
                         for node in self).splitlines()
        if lines:
            lines[1:] = [u'  %s' % ln for ln in lines[1:]]
        return text + u'\n'.join(lines).rstrip() + u'\n'

    def tail(self):
        return (self.el.tail or u'').rstrip()


class CODE(Node):
    def text(self):
        text = u'%s%s' % (
            self.el.text or u'',
            u''.join(unicode(node) for node in self),
            )
        if self.blackboard.get('pre'):
            return text
        else:
            if u'`' in text:
                return u'``%s``' % text
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


class IMG(Node):
    def text(self):
        el = self.el
        return u'![%(alt)s](<%(src)s>)' % {
            'alt': escape(el.attrib.get('alt', u''), u'[]'),
            'src': escape(el.attrib.get('src', u''), u'()')}

    def tail(self):
        return super(IMG, self).tail() or u' '


class HR(Block):
    def text(self):
        return u'---'


class DIV(Block):
    def text(self):
        return u'<div>%s%s</div>' % (
            (self.el.text or u''),
            u''.join(unicode(node) for node in self),
            )

    def tail(self):
        return self.el.tail or u''


class H1(Block):
    def text(self):
        text = super(H1, self).text()
        return u'\n%s\n%s\n' % (text, len(text) * '=')


class H2(Block):
    def text(self):
        text = super(H2, self).text()
        return u'\n%s\n%s\n' % (text, len(text) * '-')


class H3(Block):
    def text(self):
        return u'\n### %s ###' % super(H3, self).text()


class H4(Block):
    def text(self):
        return u'\n### %s ###' % super(H4, self).text()


class H5(Block):
    def text(self):
        return u'\n##### %s #####' % super(H5, self).text()


class H6(Block):
    def text(self):
        return u'\n###### %s ######' % super(H6, self).text()
