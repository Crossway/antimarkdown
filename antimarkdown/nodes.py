# -*- coding: utf-8 -*-
"""antimarkdown.nodes -- text nodes and their rendering behavior.
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


NORMALIZE_NEWLINES_CP = re.compile(ur'\n\n+', re.MULTILINE)


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
            (self.el.text or u'').lstrip(),
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
        if el.attrib.get('href') == el.text:
            return u'<%s>' % super(A, self).text()
        else:
            return u"[%(text)s](<%(href)s>%(title)s)" % {
                'text': escape(super(A, self).text(), u'[]'),
                'title': (u' "%s"' % escape(el.attrib['title'], u'()')) if 'title' in el.attrib else u'',
                'href': escape(el.attrib.get('href'), u'()')
                }


class PRE(Block):
    def text(self):
        self.blackboard['pre'] = True
        result = u'\n'.join(u'    %s' % n for n in super(PRE, self).text().splitlines())
        del self.blackboard['pre']
        return result


class BLOCKQUOTE(Block):
    NORMALIZE_BLOCKQUOTES_LEADING_CP = re.compile(ur'(^[^>]*\n)(?: *> *\n)+', re.MULTILINE)
    NORMALIZE_BLOCKQUOTES_TRAILING_CP = re.compile(ur'^(?: *> +\n)+(?! *>)', re.MULTILINE)
    
    def text(self):
        text = super(BLOCKQUOTE, self).text()
        lines = [u'> %s' % n for n in text.splitlines()]
        if lines[0].strip() == u'>':
            lines[0] = u''
        if lines[-1].strip() == u'>':
            lines[-1] = u''
        text = u'\n'.join(lines)
        text = self.NORMALIZE_BLOCKQUOTES_LEADING_CP.sub(ur'\1', text)
        text = self.NORMALIZE_BLOCKQUOTES_TRAILING_CP.sub(u'\n', text)
        return text


class OL(Block):
    def text(self):
        self.blackboard.setdefault('li-style', []).append(u'1. ')
        return super(OL, self).text()


class UL(Block):
    def text(self):
        self.blackboard.setdefault('li-style', []).append(u'* ')
        return super(UL, self).text()


class LI(Block):
    def text(self):
        li = self.blackboard.get('li-style', [u'* '])[0]
        lines = super(LI, self).text().splitlines()
        lines[0] = li + lines[0]
        if len(lines) > 1:
            lines[1:] = [u'  %s' % ln for ln in lines[1:]]
        return u'\n'.join(lines)

    def tail(self):
        return (self.el.tail or u'').rstrip() + u'\n'


class CODE(Node):
    def text(self):
        text = super(CODE, self).text()
        if self.blackboard.get('pre'):
            return text
        else:
            return u'`%s`' % text


class IMG(Node):
    def text(self):
        el = self.el
        return u'![%(alt)s](<%(src)s>)' % {
            'alt': escape(el.attrib.get('alt', u''), u'[]'),
            'src': escape(el.attrib.get('src', u''), u'()')}

    def tail(self):
        return super(IMG, self).tail() or u' '
