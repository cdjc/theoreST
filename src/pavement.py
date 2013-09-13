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
    override_text = ''
    options.builder = 'latex'
    if not hasattr(options, 'tags'):
        options.tags = []
    if hasattr(options, 'pdf_paper_size'):
        override_text += "latex_elements['paper_size'] = '"+options.pdf_paper_size+"'"
    #options.tags.append('standalone')
    #print('options:',options)
    for book, bookdir in options.books.items():
        book_options = options
        book_options.docroot = bookdir
        book_options.conf_overrides['project'] = book
        conf_override(bookdir, {'override_text' : override_text})
        pdffile = os.path.join(bookdir, options.builddir, 'latex', book+'.pdf')
        if os.path.exists(pdffile):
            os.unlink(pdffile)
        rval = paversphinx.run_sphinx(options)
        
        run_latex(os.path.join(bookdir, options.builddir, 'latex'))
        
        if os.path.exists(pdffile):
            print('copy',pdffile,bookdir)
            shutil.copy(pdffile, bookdir)
        else:
            print('pdf file not created')
    uncog()
        
def bookgroups():
    
    def is_excluded(group):
        return group.startswith('_') or group in ('out','src','common_rest')
    
    files = glob.glob(os.path.join(basepath,'*'))
    dirs = [os.path.basename(f) for f in files if os.path.isdir(f)]
    return [f for f in dirs if not is_excluded(f)]

def run_latex(builddir):
    with pushd(builddir) as old_dir:
        for texfile in glob.glob('*.tex'):
            sh('rubber --pdf '+texfile)

def conf_override(bookdir, defines_dict=None):
    conf_override_path = os.path.join(bookdir,'conf_override.py')
    if os.path.exists(conf_override_path):
        if defines_dict == None:
            defines_dict = {}
        options.cog = Bunch(basedir=bookdir,
                            pattern='conf.py',
                            includedir=bookdir,
                            defines=defines_dict)
        paver.doctools.cog(options)    

def uncog():
    options.cog = Bunch(basedir='.',
                        pattern='conf_common.py')
    paver.doctools.uncog(options)    

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
    #options.tags.append('standalone')
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
    uncog()

@task
@consume_args
def epub(args):
    handle_options(args)
    options.builder = 'epub'
    if not hasattr(options, 'tags'):
        options.tags = []
    #options.tags.append('standalone')
    options.conf_overrides['html_theme'] = 'default'
    #options.conf_overrides['html_theme_options'] = {'nosidebar' : True}
    #print('options:',options)
    for book, bookdir in options.books.items():
        book_options = options
        book_options.docroot = bookdir
        book_options.conf_overrides['project'] = book

        conf_override(bookdir)
        
        paversphinx.run_sphinx(options)
        epubfile = os.path.join(bookdir, options.builddir, 'epub', book+'.epub')
        print('copy',epubfile,bookdir)
        shutil.copy(epubfile, bookdir)

@task
@consume_args
def pseudo(args):
    handle_options(args)
    options.builder = 'pseudoxml'
    
    for book, bookdir in options.books.items():
        book_options = options
        book_options.docroot = bookdir
        book_options.conf_overrides['project'] = book

        conf_override(bookdir)
        
        paversphinx.run_sphinx(options)    

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
    options.conf_overrides['standalone'] = False
    paversphinx.run_sphinx(options, 'html')


@task
@consume_args
def html(args):
    all(args)

if __name__ == '__main__':
    from pkg_resources import load_entry_point

    sys.exit(
        load_entry_point('Paver==1.2.0', 'console_scripts', 'paver')()
    )
