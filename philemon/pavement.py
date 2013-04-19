import sys

sys.path += ['.']

from paver.easy import *
import paver.doctools
from paver.setuputils import setup
from paver.path import pushd

from docutils.parsers.rst import roles
from docutils import nodes
from verses import Parser, ParseException

def bibleref_esvapi_esv(ref):
    arg = str(ref.book)+' '+str(ref.chapter)+':'+str(ref.verse)
    if ref.to_verse:
        arg += '-'+str(ref.to_verse)
    arg = arg.replace(' ','+')
    s = 'http://www.esvapi.org/v2/rest/passageQuery?key=IP&passage='+arg
    return s

def bibleref_biblegateway(ref, version):
    arg = str(ref.book)+' '+str(ref.chapter)+':'+str(ref.verse)
    if ref.to_verse:
        arg += '-'+str(ref.to_verse)
    arg = arg.replace(' ','%20')
    s = 'http://www.biblegateway.com/passage/?search='+arg+'&version='+version
    return s
    
def bibleref_biblegateway_nasb(ref):
    return bibleref_biblegateway(ref, 'NASB')

bibleref_function = bibleref_esvapi_esv
#bibleref_function = bibleref_biblegateway_nasb

def verse_reference_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    print(role,' - ',rawtext,' - ',text,file=sys.stderr)
    p = Parser(text)
    try:
        vrlist = p.parse_verse_references()
    except ParseException as pe:
        msg = inliner.reporter.error("Exception parsing '"+text+"':"+str(pe), line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]
    nodels = []
    for vr in vrlist:
        print('refuri is',bibleref_function(vr),file=sys.stderr)
        node = nodes.reference(rawtext, vr.text, refuri=bibleref_function(vr), **options)
        nodels.append(node)
        nodels.append(nodes.generated(', ',', ', **options))
    return nodels,[]

roles.register_local_role('verse', verse_reference_role)

from docutils.core import publish_file as rundoc

from bibleref_standalone import Reader

out = 'out'
bible = 'KJV'
#print(dir())
#print(dir(path))

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
