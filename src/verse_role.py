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
    
def bibleref_biblegateway_generic(version):
    def fn(ref):
        return bibleref_biblegateway(ref, version)
    return fn

bibleref_function = None

version_reference_functions = \
{ 'KJV': bibleref_biblegateway_generic('KJV'),
  'ESV': bibleref_biblegateway_generic('ESV'),
  'NET': bibleref_biblegateway_generic('NET'),
  'HCV': bibleref_biblegateway_generic('HCV'), # Haitian Creole version (Latin alpha)
  'ICELAND': bibleref_biblegateway_generic('ICELAND'), #(Latin plus extra)
  'MNT': bibleref_biblegateway_generic('MNT'), # Macedonian (cyrillic)
  'NASB': bibleref_biblegateway_generic('NASB'),
  }

def verse_reference_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    #print(role,' - ',rawtext,' - ',text,file=sys.stderr)
    env = inliner.document.settings.env
    bible_version = env.app.config.bible_version
    if bible_version not in version_reference_functions:
        raise Exception("Unknown bible version. I don't know about "+bible_version)
    bibleref_function = version_reference_functions[bible_version]
    p = Parser(text)
    try:
        vrlist = p.parse_verse_references()
    except ParseException as pe:
        #print(pe)
        msg = inliner.reporter.error("Exception parsing '"+text+"':"+str(pe), line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]
    nodels = []
    roles.set_classes(options)
    for vr in vrlist:
        #print('refuri is',bibleref_function(vr),file=sys.stderr)
        #print('opts:',options)
        node = nodes.reference(rawtext, vr.text, internal=False, refuri=bibleref_function(vr), **options)
        nodels.append(node)
        nodels.append(nodes.generated(', ',', ', **options))
    if len(nodels) > 1:
        del nodels[-1] # delete last comma
    return nodels,[]

#def set_version(version):
    #global bibleref_function
    #if version in version_reference_functions:
        #bibleref_function = version_reference_functions[version]
    #else:
        #raise Exception("Unknown bible version:"+str(version))

#roles.register_local_role('verse', verse_reference_role)
