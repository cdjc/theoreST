#!/usr/bin/env python3

import sys,os,shutil,glob

from paver.easy import *
import paver.doctools
from paver.path import pushd

sys.path.insert(0,'.')

import paversphinx
import utils

basepath = os.path.abspath('..')

options.docroot = basepath
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
    #print('options:',options)
    for book, bookdir in options.books.items():
        book_options = options
        book_options.docroot = bookdir
        book_options.conf_overrides['project'] = book
        conf_override(bookdir)
        paversphinx.run_sphinx(options)
        run_latex(os.path.join(bookdir, options.builddir, 'latex'))
        copy_to_htmldir(options, bookdir, 'latex', book+'.pdf')
        
def bookgroups():
    
    def is_excluded(group):
        return group.startswith('_') or group in ('out','src','common_rest')
    
    files = glob.glob(os.path.join(basepath,'*'))
    dirs = [os.path.basename(f) for f in files if os.path.isdir(f)]
    return [f for f in dirs if not is_excluded(f)]


def copy_to_htmldir(options, bookdir, output_type, filename):
    #print('bookgroup',bookgroups())
    groups = [d for d in utils.splitall(bookdir) if d in bookgroups()]
    if len(groups) == 0:
        print('no groups in '+bookdir)
        return
    if len(groups) > 1:
        print('too many groups in '+bookdir)
        return
    group = groups[0]
    
    copyfile = os.path.join(bookdir, options.builddir, output_type, filename)
    copyto_dir = os.path.join(basepath, options.builddir, 'html',group)
    print('cp',copyfile,copyto_dir)
    shutil.copy(copyfile, copyto_dir)
    #print('copy',os.path.join(bookdir, options.builddir, output_type, filename))
    #print('to',os.path.join(basepath, options.builddir, 'html',group))
        
def run_latex(builddir):
    with pushd(builddir) as old_dir:
        for texfile in glob.glob('*.tex'):
            sh('rubber --pdf '+texfile)

def conf_override(bookdir):
    conf_override_path = os.path.join(bookdir,'conf_override.py')
    #print('over path:',conf_override_path)
    if os.path.exists(conf_override_path):
        options.cog = Bunch(basedir=bookdir,
                            pattern='conf.py',
                            includedir=bookdir)
        paver.doctools.cog(options)    

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
    #print('options:',options)
    for book, bookdir in options.books.items():
        book_options = options
        book_options.docroot = bookdir
        book_options.conf_overrides['project'] = book

        conf_override(bookdir)
        
        paversphinx.run_sphinx(options)
        
        in_fname = os.path.join(bookdir,options.builddir,'singlehtml','index.html')
        out_fname = os.path.join(bookdir,options.builddir,'singlehtml',book+'.html')
        insert_gdoc_css(in_fname, out_fname)

@task
@consume_args
def epub(args):
    handle_options(args)
    options.builder = 'epub'
    if not hasattr(options, 'tags'):
        options.tags = []
    options.tags.append('standalone')
    options.conf_overrides['html_theme'] = 'default'
    #options.conf_overrides['html_theme_options'] = {'nosidebar' : True}
    #print('options:',options)
    for book, bookdir in options.books.items():
        book_options = options
        book_options.docroot = bookdir
        book_options.conf_overrides['project'] = book

        conf_override(bookdir)
        
        paversphinx.run_sphinx(options)
        copy_to_htmldir(options, bookdir, 'epub', book+'.epub')
        

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
