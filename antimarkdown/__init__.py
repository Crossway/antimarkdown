# -*- coding: utf-8 -*-
"""antimarkdown -- convert Markdown to HTML.
"""
from lxml import html
from lxml.builder import E

from . import handlers


default_safe_tags = set('p blockquote i em strong b u a h1 h2 h3 h4 h5 h6 hr pre code div br img ul ol li span'.split())
default_safe_attrs = set('href src alt style title'.split())


def to_markdown(html_string, safe_tags=None, safe_attrs=None):
    """Convert the given HTML text fragment to Markdown.
    """
    # out = StringIO()
    # for f in parse_fragments(html_string, safe_tags=None, safe_attrs=None):
    #     handlers.process_tag_events(f, out)
    # return normalize(out.getvalue())
    return handlers.render(*parse_fragments(html_string, safe_tags))


def parse_fragments(html_string, safe_tags=None, safe_attrs=None):
    """Parse HTML fragments from the given HTML fragment string.
    """
    for f in html.fragments_fromstring(html_string):
        cf = clean_fragment(f, safe_tags=safe_tags, safe_attrs=safe_attrs)
        if cf is not None:
            yield cf


def clean_fragment(subtree, safe_tags=None, safe_attrs=None):
    """Clean an HTML fragment subtree of unsafe tags and attrs.
    """
    if isinstance(subtree, str):
        return E('p', subtree)

    if safe_tags is None:
        safe_tags = default_safe_tags
    if safe_attrs is None:
        safe_attrs = default_safe_attrs

    if subtree.tag not in safe_tags:
        if callable(subtree.tag):
            # A comment...
            return None
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
