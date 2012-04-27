# -*- coding: utf-8 -*-
"""antimarkdown -- convert Markdown to HTML.
"""
import re
from BeautifulSoup import UnicodeDammit
from lxml import html
from StringIO import StringIO

import handlers


default_safe_tags = set('p blockquote i em strong b u a h1 h2 h3 pre code br img ul ol li span'.split())
default_safe_attrs = set('href src alt style title'.split())

NORMALIZE_NEWLINES_CP = re.compile(ur'\n\n+', re.MULTILINE)
NORMALIZE_BLOCKQUOTES_CP = re.compile(ur'^(?: *> +\n)+(?! *>)', re.MULTILINE)


def normalize(markdown_text):
    norm = markdown_text
    norm = NORMALIZE_BLOCKQUOTES_CP.sub(u'\n', norm)
    norm = NORMALIZE_NEWLINES_CP.sub(u'\n\n', norm)
    return norm.rstrip()


def to_markdown(html_string, safe_tags=None, safe_attrs=None):
    """Convert the given HTML text fragment to Markdown.
    """
    out = StringIO()
    for f in parse_fragments(html_string, safe_tags=None, safe_attrs=None):
        handlers.process_tag_events(f, out)
    return normalize(out.getvalue())


def parse_fragments(html_string, safe_tags=None, safe_attrs=None):
    """Parse HTML fragments from the given HTML fragment string.
    """
    return (clean_fragment(f, safe_tags=safe_tags, safe_attrs=safe_attrs)
            for f in html.fragments_fromstring(decode_html(html_string)))


def decode_html(html_string):
    """Given an HTML string fragment, produce a unicode string.
    """
    converted = UnicodeDammit(html_string, isHTML=True)
    if not converted.unicode:
        raise UnicodeDecodeError(
            "Failed to detect encoding, tried [%s]",
            ', '.join(converted.triedEncodings))
    # print converted.originalEncoding
    return converted.unicode


def clean_fragment(subtree, safe_tags=None, safe_attrs=None):
    """Clean an HTML fragment subtree of unsafe tags and attrs.
    """
    if safe_tags is None:
        safe_tags = default_safe_tags
    if safe_attrs is None:
        safe_attrs = default_safe_attrs

    if subtree.tag not in safe_tags:
        p = html.Element('p')
        p.append(subtree)
        subtree = p

    for el in list(subtree.iter()):
        if el.tag not in safe_tags:
            el.drop_tag()
        else:
            for attr in list(el.attrib.keys()):
                if attr not in safe_attrs:
                    el.attrib.pop(attr)

    return subtree
