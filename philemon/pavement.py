import sys

out = 'out'
bible = 'ESV'

sys.path += ['.', '../src']

# paver imports
from paver.easy import *
import paver.doctools
from paver.setuputils import setup
from paver.path import pushd

# docutils imports
from docutils.core import publish_file as rundoc

# my imports
import verse_role
import biblepassage

#from bibleref_standalone import Reader


@task
def ensure_dirs_exists():
    if not path.exists(out):
        path.mkdir(out)

@task
@needs(['ensure_dirs_exists'])
def philemon_latex():
    source = 'philemon.txt'
    dest = path(out) / 'philemon.tex'
    reader = path('.').abspath() / 'bibleref_standalone'
    
    rundoc(writer_name='latex',
        source_path = source,
        destination_path = dest)

@task
@needs(['ensure_dirs_exists'])
def philemon_html():
    source = 'philemon.txt'
    dest = path(out) / 'philemon.html'
    reader = path('.').abspath() / 'bibleref_standalone'

    sys.path += ['.']
    
    rundoc(writer_name='html',
        source_path = source,
        destination_path = dest)

@task
@needs(['philemon_latex'])
def philemon_pdf():
    with pushd(out) as old_dir:
        sh('pdflatex philemon.tex')

@task
def philemon_pseudo():
    source = 'philemon.txt'
    dest = path(out) / 'philemon.pxml'
    reader = path('.').abspath() / 'bibleref_standalone'

    sys.path += ['.']
    
    rundoc(writer_name='pseudoxml',
        source_path = source,
        destination_path = dest,
        reader = Reader(bible))

@task
@needs(['philemon_pdf', 'philemon_html'])
def philemon():
    pass

@task
@consume_args
def pdf(args, help_function):
    print(args)
