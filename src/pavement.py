#!/usr/bin/env python3

import sys,os,shutil,glob

from paver.easy import *

sys.path.insert(0,'.')

import paversphinx
import utils

options.docroot = '..'
options.builddir = 'out'
options.conf_overrides = {}

def handle_options(args):
    utils.parse_options(options, args)

    #print(options)

@task
@consume_args
def pdf(args):
    handle_options(args)
    options.builder = 'latex'
    if not hasattr(options, 'tags'):
        options.tags = []
    options.tags.append('standalone')
    print('options:',options)
    for book, bookdir in options.books.items():
        book_options = options
        book_options.docroot = bookdir
        book_options.conf_overrides['project'] = book
        paversphinx.run_sphinx(options)
    
@task
@consume_args
def single(args):
    '''
    For uploading (and converting) to google docs.
    '''
    handle_options(args)
    options.builder = 'singlehtml'
#    options.builder = 'epub'
    if not hasattr(options, 'tags'):
        options.tags = []
    options.tags.append('standalone')
    options.conf_overrides['html_theme'] = 'default'
    #options.conf_overrides['html_theme_options'] = {'nosidebar' : True}
    print('options:',options)
    for book, bookdir in options.books.items():
        book_options = options
        book_options.docroot = bookdir
        book_options.conf_overrides['project'] = book
        paversphinx.run_sphinx(options)
        
        in_fname = os.path.join(bookdir,options.builddir,'singlehtml','index.html')
        out_fname = os.path.join(bookdir,options.builddir,'singlehtml',book+'.html')
        insert_gdoc_css(in_fname, out_fname)

def insert_gdoc_css(in_fname, out_fname):
    with open(in_fname,'r') as fid:
        lines = fid.readlines()
    if len(lines) == 0:
        print('No lines when reading file:'+in_fname,file=sys.stderr)
        return
    shutil.copy(in_fname, in_fname+'.precss')
    dumped_css = False
    with open(out_fname,'w') as fid:
        for line in lines:
            if '<link rel="stylesheet"' in line:
                continue
            
            print(line, file=fid, end='')
            if '<head>' in line and not dumped_css:
                print('<style type="text/css">', file=fid)
                print(open('gdoc.css').read(), file=fid)
                print('</style>',file=fid)
                dumped_css = True
                

@task
def publish_local():
    print("HERE")
    pubdir = '/media/sf_EBCWA/'
    htmldir = '../out/html'
    print('Removing...')
    for f in glob.glob(os.path.join(pubdir,'*')):
        if os.path.isfile(f):
            os.unlink(f)
        elif os.path.isdir(f):
            shutil.rmtree(f)
        else:
            print("Can't remove object in "+pubdir+": "+f)

    print('Copying...')
    for f in glob.glob(os.path.join(htmldir,'*')):
        base = os.path.basename(f)
        dest = os.path.join(pubdir,base)
        if os.path.isfile(f):
            shutil.copy(f,dest)
        elif os.path.isdir(f):
            shutil.copytree(f,dest)
        else:
            print("Can't copy object "+f)
    print('Done')

@task
@consume_args
def all(args):
    handle_options(args)
    #rint('options:',options)
    paversphinx.run_sphinx(options, 'html')



if __name__ == '__main__':
    from pkg_resources import load_entry_point

    sys.exit(
        load_entry_point('Paver==1.2.0', 'console_scripts', 'paver')()
    )
