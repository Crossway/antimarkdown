# -*- coding: utf-8 -*-
"""setup.py -- setup file for antimarkdown
"""
import os
from setuptools import setup

README = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.rst')


setup(
    name = "antimarkdown",
    packages = ['antimarkdown'],
    install_requires = [
        'lxml',
    ],

    package_data = {
        '': ['*.txt', '*.html'],
    },
    zip_safe = False,

    version = "1.0.1",
    description = "HTML to Markdown converter.",
    long_description = open(README).read(),
    author = "David Eyk",
    author_email = "deyk@crossway.org",
    url = "http://github.com/Crossway/antimarkdown/",
    license = 'BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Software Development :: Documentation',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Filters',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Communications :: Email :: Filters',
    ],
)
