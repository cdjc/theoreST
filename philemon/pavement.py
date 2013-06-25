#!/usr/bin/env python3
import sys

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
import greek_role
import biblepassage

options(
    setup=dict(
        out = 'out',
        bible = 'ESV',
        source = 'philemon_end_doctrines.txt'
        #source = 'philemon.txt'
        )
    )

verse_role.set_version(options.bible)
biblepassage.set_version(options.bible)

@task
def ensure_dirs_exists():
    if not path.exists(options.out):
        path.mkdir(options.out)

@task
@needs(['ensure_dirs_exists'])
def philemon_odt():
    dest = path(options.out) / 'philemon.odt'
    
    rundoc(writer_name='odf_odt',
        source_path = options.source,
        destination_path = dest)
    
@task
@needs(['ensure_dirs_exists'])
def philemon_latex():
    dest = path(options.out) / 'philemon.tex'
    #reader = path('.').abspath() / 'bibleref_standalone'
    
    rundoc(writer_name='latex',
        source_path = options.source,
        destination_path = dest)

@task
@needs(['ensure_dirs_exists'])
def philemon_html():
    dest = path(options.out) / 'philemon.html'
    #reader = path('.').abspath() / 'bibleref_standalone'
    
    #import traceback
    #traceback.print_stack()

    sys.path += ['.']
    
    rundoc(writer_name='html',
        source_path = options.source,
        destination_path = dest)

@task
@needs(['philemon_latex'])
def philemon_pdf():
    with pushd(options.out) as old_dir:
        sh('rubber --pdf philemon.tex')

@task
def philemon_pseudo():
    dest = path(options.out) / 'philemon.pxml'
    reader = path('.').abspath() / 'bibleref_standalone'

    sys.path += ['.']
    
    rundoc(writer_name='pseudoxml',
        source_path = options.source,
        destination_path = dest)

@task
@needs(['philemon_pdf', 'philemon_html'])
def philemon():
    pass

@task
@consume_args
def pdf(args, help_function):
    print(args)


if __name__ == '__main__':
    from pkg_resources import load_entry_point

    sys.exit(
        load_entry_point('Paver==1.2.0', 'console_scripts', 'paver')()
    )
