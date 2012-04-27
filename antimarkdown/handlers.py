# -*- coding: utf-8 -*-
"""antimarkdown.handlers -- Element handlers for converting HTML Elements/subtrees to Markdown text.
"""
import re
from collections import deque, defaultdict
import operator as op
from markdown import odict

WHITESPACE_CP = re.compile(r'\s+')

ESCAPES_CP = re.compile(ur'([\\`*_\{\}\[\]\(\)>#.!+-])')


def default_text(el, kw):
    if el.text is None:
        return u''
    else:
        if kw.get('pre'):
            return u'\n'.join(u'    %s' % n for n in el.text.splitlines())
        else:
            return WHITESPACE_CP.sub(u' ', el.text.replace(u'\n', u' '))


def default_tail(el, kw):
    if el.tail is None:
        return u''
    else:
        if kw.get('pre'):
            return u'\n'.join(u'    %s' % n for n in el.tail.splitlines())
        else:
            return WHITESPACE_CP.sub(u' ', el.tail.replace(u'\n', u' '))


def escaped_default_text(el, kw):
    return ESCAPES_CP.sub(ur'\\\1', default_text(el, kw))


def escaped_default_tail(el, kw):
    return ESCAPES_CP.sub(ur'\\\1', default_tail(el, kw))


def escape(text, characters):
    for c in characters:
        text = text.replace(c, ur'\%s' % c)
    return text


# Open handlers
on_open = defaultdict(lambda: deque([default_text]))
on_open_ephem = defaultdict(deque)

on_preopen = defaultdict(deque)
on_preopen_ephem = defaultdict(deque)

on_postopen = defaultdict(deque)
on_postopen_ephem = defaultdict(deque)

# Close handlers
on_preclose = defaultdict(deque)
on_preclose_ephem = defaultdict(deque)
    
on_close = defaultdict(lambda: deque([default_tail]))
on_close_ephem = defaultdict(deque)

on_postclose = defaultdict(deque)
on_postclose_ephem = defaultdict(deque)

transforms = odict.OrderedDict()

# Event collections
open_events = deque([on_preopen, on_preopen_ephem, on_open, on_open_ephem, on_postopen, on_postopen_ephem])
close_events = deque([on_preclose, on_preclose_ephem, on_close, on_close_ephem, on_postclose, on_postclose_ephem])

open_ephem_events = deque([on_preopen_ephem, on_open_ephem, on_postopen_ephem])
close_ephem_events = deque([on_preclose_ephem, on_close_ephem, on_postclose_ephem])


def open_(tag):
    def wrap(func):
        on_open[tag] = deque([func])
        return func
    return wrap


def close_(tag):
    def wrap(func):
        on_close[tag] = deque([func])
        return func
    return wrap


def open_left(tag):
    def wrap(func):
        on_open[tag].appendleft(func)
        return func
    return wrap


def open_right(tag):
    def wrap(func):
        on_open[tag].append(func)
        return func
    return wrap


def close_left(tag):
    def wrap(func):
        on_close[tag].appendleft(func)
        return func
    return wrap


def close_right(tag):
    def wrap(func):
        on_close[tag].append(func)
        return func
    return wrap


# Specific handlers
on_open['p'] = deque([lambda el, kw: default_text(el, kw).lstrip()])


@open_('blockquote')
def open_blockquote(el, kw):
    transforms['in_blockquote'] = lambda t: t.replace('\n', '\n> ')
    return u'> ' + default_text(el, kw).lstrip()


@close_('p')
@close_('blockquote')
@close_('pre')
def close_block(el, kw):
    return u'\n\n' + (el.tail.strip() if el.tail is not None and el.tail.strip() else u'')


@close_left('blockquote')
def close_bq(el, kw):
    transforms.pop('in_blockquote')


@open_('pre')
def open_pre(el, kw):
    op.setitem(kw, 'pre', True)


@close_('pre')
def close_pre(el, kw):
    kw.pop('pre')
    return u'\n\n' + (el.tail.strip() if el.tail is not None and el.tail.strip() else u'')

on_open['code'].appendleft(lambda el, kw: u'`' if not kw.get('pre') else u'')
on_close['code'].appendleft(lambda el, kw: u'`' if not kw.get('pre') else u'')

on_open['a'] = deque([lambda el, kw: u"[" if el.attrib.get('href') != el.text else u'<%s>' % el.text])


@close_left('a')
def close_a(el, kw):
    if el.attrib.get('href') != el.text:
        return u"%s](<%s>%s)" % (escape(default_text(el, kw), u'[]'), escape(el.attrib.get('href', u''), u'()'),
                                 (u' "%s"' % escape(el.attrib['title'], u'()')) if 'title' in el.attrib else u'')

on_open['ol'] = deque([lambda el, kw: kw.setdefault('li-style', []).append(u'1. ')])
on_open['ul'] = deque([lambda el, kw: kw.setdefault('li-style', []).append(u'* ')])

on_open['li'] = deque([lambda el, kw: kw.get('li-style', [u'* '])[0] + default_text(el, kw).lstrip()])
on_close['li'] = deque([lambda el, kw: default_tail(el, kw).strip(),
                        lambda el, kw: u'\n'])


@close_left('ol')
@close_left('ul')
def close_list(el, kw):
    kw.setdefault('li-style', [None]).pop()
    return u'\n'


on_open['img'] = deque([lambda el, kw: u'![%s](<%s>)' % (escape(el.attrib.get('alt', u''), u'[]'),
                                                         escape(el.attrib.get('src', u''), u'()'))])
on_close['img'] = deque([lambda el, kw: default_tail(el, kw) or u' '])


def write(text_out, out_buffer):
    for transform in transforms.itervalues():
        text_out = transform(text_out)
    out_buffer.write(text_out)
    

def process_tag_events(subtree, out_buffer):
    """Process an ElementTree subtree and send tag events to handlers.
    """
    opened = set()
    stack = deque([subtree])
    blackboard = {}

    while stack:
        subtree = stack.pop()

        if subtree not in opened:
            # Open the subtree
            # print "Opening", subtree.tag
            for events in open_events:
                for handler in events[subtree.tag]:
                    result = handler(subtree, blackboard)
                    if result is not None:
                        write(result, out_buffer)

            # Clear ephemeral events
            for events in open_ephem_events:
                events.clear()

            stack.append(subtree)
            
            # Queue children
            for el in reversed(subtree):
                stack.append(el)

            opened.add(subtree)
        else:
            # Close the subtree
            # print "Closing", subtree.tag
            for events in close_events:
                for handler in events[subtree.tag]:
                    result = handler(subtree, blackboard)
                    if result is not None:
                        write(result, out_buffer)

            # Clear ephemeral events
            for events in close_ephem_events:
                events.clear()
