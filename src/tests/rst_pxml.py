#!/usr/bin/python3

# $Id: rst2pseudoxml.py 4564 2006-05-21 20:44:42Z wiemann $
# Author: David Goodger <goodger@python.org>
# Copyright: This module has been placed in the public domain.

"""
A minimal front end to the Docutils Publisher, producing pseudo-XML.
"""

try:
    import locale
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.core import publish_cmdline, default_description

from docutils.parsers.rst import directives

import sys
sys.path.append('..')
from bibleyves import BiblePassageYVES

directives.register_directive('biblepassage', BiblePassageYVES)


description = ('Tests standalone reStructuredText. ' + default_description)

publish_cmdline(writer_name='pseudoxml',description=description)
#publish_cmdline(writer_name='html',description=description)
