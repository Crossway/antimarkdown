# -*- coding: utf-8 -*-
'''html2markdown_steps -- feature step implementations for the antimarkdown HTML-to-Markdown translator.
'''
from lxml import html, etree
from antimarkdown import nodes
from behave import when, then
import antimarkdown
import codecs
import difflib
import html5lib
import markdown


parser = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder('lxml'), namespaceHTMLElements=False)


def tidy(src, fragment=False, container='div', encoding=None, parseMeta=True, useChardet=True,
         method='xml', pretty_print=False, xml_declaration=None, output_encoding='utf-8'):
    if fragment:
        parts = parser.parseFragment(src, container=container, encoding=encoding,
                                     parseMeta=parseMeta, useChardet=useChardet)
    else:
        parts = [parser.parse(src, encoding=encoding, parseMeta=parseMeta, useChardet=useChardet)]

    ret = ''
    for p in parts:
        if (type(p) == str):
            ret += p
        else:
            ret += etree.tostring(p, method=method, pretty_print=pretty_print, xml_declaration=xml_declaration,
                                  encoding=output_encoding).decode('utf-8')
    return ret


def normalize_html(html_text):
    html_text = '\n'.join(html.tostring(el).decode('utf-8')
                          for el in antimarkdown.parse_fragments(html_text))
    tidied = tidy('\n'.join(line.strip()
                  for line in nodes.whitespace(html_text.strip())
                                   .replace('>', '>\n')
                                   .splitlines()).strip())
    return tidied


@when('I translate the Markdown file to HTML using markdown')
def step_translate_markdown_to_HTML(context):
    with codecs.open(context.markdown_path, encoding='utf-8') as fi:
        md = context.markdown_text = fi.read()
    context.translated_html_text = normalize_html(markdown.markdown(md))


@then('the resulting HTML should match the corresponding text in the Markdown file.')
def step_HTML_matches_MD(context):
    with codecs.open(context.html_path, encoding='utf-8') as fi:
        html = context.html_text = normalize_html(fi.read().rstrip())
    assert context.translated_html_text == html, '\nDifferences:\n' + '\n'.join(
        difflib.context_diff([n for n in context.translated_html_text.splitlines()],
                             [n for n in html.splitlines()],
                             fromfile='Got', tofile='Expected'))
