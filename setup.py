# -*- coding: utf-8 -*-
"""setup.py -- setup file for markdown-hilite
"""
from setuptools import setup

setup(
    name = "antimarkdown",
    packages = ['antimarkdown'],
    install_requires = [
        'lxml',
        'BeautifulSoup',
        ],

    package_data = {
        '': ['*.txt', '*.html'],
        },
    zip_safe = False,

    version = "0.1",
    description = "HTML to Markdown converter.",
    author = "David Eyk",
    author_email = "deyk@crossway.org",
    )
