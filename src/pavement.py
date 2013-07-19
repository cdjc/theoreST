#!/usr/bin/env python3
import sys, os

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
        #source = 'philemon.txt',
        draft = True
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

if not options.draft:
    docutil_settings['strip_elements_with_classes'] = ['comment']

@task
def ensure_dirs_exists():
    dirs = [options.out,
            os.path.join(options.out, 'html')]
    for path in dirs:
        if not os.path.exists(path):
            os.mkdir(path)
    

@task
@needs(['ensure_dirs_exists'])
def philemon_odt():
    dest = path(options.out) / 'philemon.odt'
    
    rundoc(writer_name='odf_odt',
        source_path = options.source,
        settings_overrides=docutil_settings,
        destination_path = dest)
    
@task
@needs(['ensure_dirs_exists'])
def philemon_latex():
    dest = path(options.out) / 'philemon.tex'
    
    rundoc(writer_name='latex',
        source_path = options.source,
        settings_overrides=docutil_settings,
        destination_path = dest)

@task
@needs(['ensure_dirs_exists'])
@consume_args
def html(args):
    print('args',args)
    opts = utils.parse_options(args)

    if opts['bible_version'] != None:
        options.bible = opts['bible_version']
        verse_role.set_version(options.bible)
        biblepassage.set_version(options.bible)

    if opts['draft']:
        docutil_settings['strip_elements_with_classes'] = ['comment']

    for book in opts['books']:
        source = os.path.join('..',book,book+'.txt')
        dest = os.path.join(options.out, 'html', book+'.html')
                              
        #dest = path(options.out) / 'philemon.html'
    
        #sys.path += ['.']
        
        rundoc(writer_name='html',
            source_path = source,
            settings_overrides=docutil_settings,
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
        settings_overrides=docutil_settings,
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
