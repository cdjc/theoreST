import sys

from docutils.parsers.rst import roles
from docutils import nodes

from verse_parser import Parser, ParseException

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

def bibleref_biblegateway_kjv(ref):
    return bibleref_biblegateway(ref, 'KJV')

def bibleref_biblegateway_generic(version):
    def fn(ref):
        return bibleref_biblegateway(ref, version)
    return fn

bibleref_function = None

version_reference_functions = \
{ 'KJV': bibleref_biblegateway_generic('KJV'),
  'ESV': bibleref_biblegateway_generic('ESV'),
  'NET': bibleref_biblegateway_generic('NET'),
  'NASB': bibleref_biblegateway_generic('NASB'),
  }

def verse_reference_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    #print(role,' - ',rawtext,' - ',text,file=sys.stderr)
    if bibleref_function == None:
        raise Exception("No bible set. Call set_version() after import")
    p = Parser(text)
    try:
        vrlist = p.parse_verse_references()
    except ParseException as pe:
        msg = inliner.reporter.error("Exception parsing '"+text+"':"+str(pe), line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]
    nodels = []
    for vr in vrlist:
        #print('refuri is',bibleref_function(vr),file=sys.stderr)
        node = nodes.reference(rawtext, vr.text, refuri=bibleref_function(vr), **options)
        nodels.append(node)
        nodels.append(nodes.generated(', ',', ', **options))
    if len(nodels) > 1:
        del nodels[-1] # delete last comma
    return nodels,[]

def set_version(version):
    global bibleref_function
    if version in version_reference_functions:
        bibleref_function = version_reference_functions[version]
    else:
        raise Exception("Unknown bible version:"+str(version))

roles.register_local_role('verse', verse_reference_role)
