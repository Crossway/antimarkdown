# -*- coding: utf-8 -*-
"""html2markdown_steps -- feature step implementations for the antimarkdown HTML-to-Markdown translator.
"""
import codecs
import difflib
from behave import *

from html5tidy import tidy

from lxml import html
import antimarkdown
from antimarkdown import nodes


def normalize_html(html_text):
    html_text = '\n'.join(html.tostring(el, encoding=str)
                           for el in antimarkdown.parse_fragments(html_text))
    tidied = tidy(
        '\n'.join(line.strip()
                   for line in nodes.whitespace(html_text.strip()).replace('>', '>\n').splitlines()),
        pretty_print=True)
    return tidied.decode('utf-8')


@when('I translate the Markdown file to HTML using markdown')
def step_translate_markdown_to_HTML(context):
    import markdown
    with codecs.open(context.markdown_path, encoding='utf-8') as fi:
        md = context.markdown_text = fi.read()
    context.translated_html_text = normalize_html(markdown.markdown(md))


@then('the resulting HTML should match the corresponding text in the Markdown file.')
def step_HTML_matches_MD(context):
    with codecs.open(context.html_path, encoding='utf-8') as fi:
        html = context.html_text = normalize_html(fi.read())
    assert context.translated_html_text == html, '\nDifferences:\n' + '\n'.join(
        difflib.context_diff([n.encode('ascii', 'replace')
                              for n in context.translated_html_text.splitlines()],
                             [n.encode('ascii', 'replace')
                              for n in html.splitlines()],
                             fromfile='Got', tofile='Expected'))
    # assert context.translated_html_text == html, '\nDifferences:\n' + '\n'.join(
    #     difflib.context_diff([repr(n) for n in context.translated_html_text.splitlines()],
    #                          [repr(n) for n in html.splitlines()],
    #                          fromfile='Got', tofile='Expected'))
