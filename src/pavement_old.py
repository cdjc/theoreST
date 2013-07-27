#!/usr/bin/env python3
import sys, os
import shutil

sys.path += ['.', '../src']

# paver imports
from paver.easy import *
import paver.doctools
from paver.setuputils import setup
from paver.path import pushd

# docutils imports
from docutils.core import publish_file as rundoc

options(
    setup=dict(
        out = 'out',
        bible = 'ESV',
        draft = False
        )
    )

# my imports
import verse_role
import greek_role
import biblepassage
import utils

verse_role.set_version(options.bible)
biblepassage.set_version(options.bible)

docutil_settings = {}

def handle_options(args):
    utils.parse_options(options, args)

    print(options)
    if options.bible != None:
        verse_role.set_version(options.bible)
        biblepassage.set_version(options.bible)

    if not options.draft:
        #print('NOT DRAFT')
        docutil_settings['strip_elements_with_classes'] = ['comment']
    else:
        #print('DRAFT')
        if 'strip_elements_with_classes' in docutil_settings:
            del docutil_settings['strip_elements_with_classes']
    
@task
def ensure_dirs_exists():
    dirs = [options.out,
            os.path.join(options.out, 'html'),
            os.path.join(options.out, 'tex'),
            os.path.join(options.out, 'pdf')
            ]
    for path in dirs:
        if not os.path.exists(path):
            os.mkdir(path)

#@task
#@needs(['ensure_dirs_exists'])
#def philemon_odt():
    #dest = path(options.out) / 'philemon.odt'
    
    #rundoc(writer_name='odf_odt',
        #source_path = options.source,
        #settings_overrides=docutil_settings,
        #destination_path = dest)
    
@task
@needs(['ensure_dirs_exists'])
@consume_args
def latex(args):
    handle_options(args)
    
    for book in options.books:
        print('---',book,'---')
        source = os.path.join('..',book,book+'.txt')
        dest = os.path.join(options.out, 'tex', book+'.tex')

        rundoc(writer_name='latex',
               source_path = source,
               settings_overrides=docutil_settings,
               destination_path = dest)

@task
@needs(['ensure_dirs_exists'])
@consume_args
def html(args):
    handle_options(args)

    for book in options.books:
        print('---',book,'---')
        source = os.path.join('..',book,book+'.txt')
        dest = os.path.join(options.out, 'html', book+'.html')
                              
        rundoc(writer_name='html',
            source_path = source,
            settings_overrides=docutil_settings,
            destination_path = dest)

@task
@needs(['latex'])
@consume_args
def pdf(args):
    texdir = os.path.join(options.out, 'tex')
    pdfdir = os.path.join('..', 'pdf')
    for book in options.books:
        with pushd(texdir) as old_dir:
            texfile = book+'.tex'
            pdffile = book+'.pdf'
            sh('rubber --pdf '+texfile)
            if os.path.isfile(pdffile):
                shutil.copy(pdffile, pdfdir)

#@task
#def philemon_pseudo():
    #dest = path(options.out) / 'philemon.pxml'
    #reader = path('.').abspath() / 'bibleref_standalone'

    #sys.path += ['.']
    
    #rundoc(writer_name='pseudoxml',
        #source_path = options.source,
        #settings_overrides=docutil_settings,
        #destination_path = dest)



if __name__ == '__main__':
    from pkg_resources import load_entry_point

    sys.exit(
        load_entry_point('Paver==1.2.0', 'console_scripts', 'paver')()
    )
