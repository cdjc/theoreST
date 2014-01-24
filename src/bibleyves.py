#!/usr/bin/env python3

import os
import sys

import xml.etree.ElementTree as etree

from docutils.parsers.rst import roles, Directive, directives
from docutils import nodes

import verse_parser

class BiblePassageYVES(Directive):
    required_arguments = 1
    optional_aguments = 0
    final_argument_whitespace = True
    version = None
    option_spec = {'bold':directives.flag,
                   'title':directives.unchanged}
    
    preamble = r'''

.. raw:: latex
    
    \begin{minipage}[c]{\textwidth}
    
'''
    
    postamble = r'''
    
.. raw:: latex
    
    \end{minipage} 
    
'''

    def run(self):
        try:
            env = self.state.document.settings.env
            #version = env.config.bible_version
            print('options:',self.options, file=sys.stderr)
            if 'bible_version' not in env.config:
                raise self.error("BiblePassage: no bible version. Call set_version() after biblepassage import")
        except AttributeError:
            # probably running from docutils rather than sphionx
            pass
        ref = self.arguments[0]
        if 'title' in self.options and self.options['title'] == '':
            self.options['title'] = ref
        #print('options:',self.options, file=sys.stderr)
        vp = verse_parser.Parser(ref)
        try:
            vrefs = vp.parse_verse_references()
        except verse_parser.ParseException as pe:
            raise self.error("BiblePassage: parse verse ref error: "+str(pe))
        if len(vrefs) != 1:
            raise self.error("BiblePassage: One, and only one, verse reference allowed")
        vref = vrefs[0]
         
        #verse = vref.verse.value if vref.verse else None
        #to_verse = vref.to_verse.value if vref.to_verse else None
        #print('Book',type(vref.book),'Chapter',vref.chapter)
        y = YvesReader()
        nodes = y.rst_nodes(self.options,
                            'NET',
                            str(vref.book),
                            vref.chapter.value, 
                            vref.verse.value if vref.verse else None,
                            vref.to_verse.value if vref.to_verse else None)
        return nodes
        
        
class TextWriter(object):
    
    def __init__(self):
        self.show_label = False
    
    def span_content(self, elem, depth):
        if elem.text.strip():
            print(elem.text, end='')
        
    def span_ft(self,elem, depth):
        print('[ft]', end='')
        
    def div_p(self, elem, depth):
        print()
        
    def span_verse(self, elem, depth):
        self.show_label = True
        
    def span_label(self, elem, depth):
        if self.show_label:
            print(elem.text+' ', end='')
            self.show_label = False
            
    def span_bd(self, elem, depth): # bold
        pass
        
    def span_it(self, elem, depth): # italics
        pass
        
    def span_sc(self, elem, depth): # small caps
        pass #print(elem.text.upper(), end='')
        
    def span_nd(self, elem, depth): # name of God (Deity)
        pass
        
    def div_b(self, elem, depth):
        pass
        
    def div_s1(self, elem, depth):
        pass
        
    def span_heading(self, elem, depth):
        pass
        
    def div_q1(self, elem, depth):
        print()
        print('  ', end='')

    def div_q2(self, elem, depth):
        print()
        print('    ', end='')
        
    def span_qs(self, elem, depth): # selah
        print()
        print(' '*40, end='')
        
    def unknown(self, elem_name, depth):
        print('\n'+'-'*40+'\nUnknown elem:'+elem_name)

class RstWriter(object):
    
    def __init__(self, options, from_verse = None, to_verse = None):
        self.options = options
        self.node_stack = [(nodes.block_quote(), 0)] # node, depth
        self.is_first = True
        self.show_label = False
        self.current_verse = 0 # TODO: Need to handle some psalms that have a 'verse 0'
        self.from_verse = from_verse
        if self.from_verse is not None and to_verse is None:
            self.to_verse = from_verse
        else:
            self.to_verse = to_verse
        if 'title' in options:
            title = nodes.Text(options['title'])
            line = nodes.line()
            line_block = nodes.line_block()
            line.append(title)
            line_block.append(line)
            self.node_stack[0][0].append(line_block)

    def get_base_node(self):
        self._unwind_stack()
        base_node = self.node_stack[0][0]
        if 'bold' in self.options:
            bold_node = nodes.strong()
            bold_node.append(base_node)
            return bold_node
        return base_node

    def _update_stack(self, item, depth):
        if not self.verse_wanted():
            return
        if self.is_first:
            self.is_first = False
            self._update_stack(nodes.line_block(), depth - 2)
            self._update_stack(nodes.line(), depth - 1)
        tos,tos_depth = self.node_stack[-1]
        while depth <= tos_depth:
            del self.node_stack[-1]
            old_node = tos
            tos,tos_depth = self.node_stack[-1]
            tos.append(old_node)
        self.node_stack.append((item, depth))
        
    def _unwind_stack(self):
        while len(self.node_stack) > 1:
            self.node_stack[-2][0].append(self.node_stack[-1][0])
            del self.node_stack[-1]
        
    def verse_wanted(self):
        if self.from_verse is None:
            return True
        return self.from_verse <= self.current_verse <= self.to_verse
    
    def span_content(self, elem, depth):
        if elem.text.strip():
            self._update_stack(nodes.Text(elem.text), depth)
        
    def span_ft(self,elem, depth):
        pass
        #print('[ft]', end='')
        
    def div_p(self, elem, depth):
        self._update_stack(nodes.line_block(), depth - 1)
        self._update_stack(nodes.line(), depth)
        
    def span_verse(self, elem, depth):
        self.show_label = True
        
    def span_label(self, elem, depth):
        if self.show_label:
            self.current_verse = int(elem.text)
            self._update_stack(nodes.Text(elem.text+' '), depth)
            self.show_label = False
            
    def span_bd(self, elem, depth): # bold
        pass
        
    def span_it(self, elem, depth): # italics
        italics = nodes.emphasis()
        self._update_stack(italics, depth)
        #print('italics')
        pass
        
    def span_sc(self, elem, depth): # small caps
        pass #print(elem.text.upper(), end='')
        
    def span_nd(self, elem, depth): # name of God (Deity)
        pass
        
    def div_b(self, elem, depth):
        pass
        
    def div_s1(self, elem, depth):
        pass
        
    def span_heading(self, elem, depth):
        pass
        
    def div_q1(self, elem, depth):
        print()
        print('  ', end='')

    def div_q2(self, elem, depth):
        print()
        print('    ', end='')
        
    def span_qs(self, elem, depth): # selah
        print()
        print(' '*40, end='')
        
    def unknown(self, elem_name, depth):
        if elem_name in ('div_version',
                         'div_book',
                         'div_chapter',
                         'div_label'):
            return
        print('\n'+'-'*40+'\nUnknown elem:'+elem_name, file=sys.stderr)

class ProcessYvesXML(object):
    
    ignore_names = set(('span_body','span_note'))
    
    def __init__(self, xml):
        self.xml = xml
            
    def process(self, writer):
        self.writer = writer
        root = etree.fromstring(self.xml)
        self.process_elem(root, 1)
            
    def process_elem(self, elem, depth):
        tag = elem.tag
        
        if 'class' in elem.attrib:
            klass = elem.attrib['class'].strip().split()[0]
        else:
            klass=''
        elem_name = tag+'_'+klass
        #print(' '*(depth-1)+elem_name)
        if elem_name not in self.ignore_names:
            #print(elem_name, depth)
            if hasattr(self.writer, elem_name):
                method = getattr(self.writer, elem_name)
                method(elem, depth)
            else:
                self.writer.unknown(elem_name, depth)
        self.process_children(elem, depth)
            
    def process_children(self, elem, depth):
        for child in elem.getchildren():
            self.process_elem(child, depth + 1)
        

class YvesReader:

    yves_dir = '/home/theorest/yves'
    book_codes = {'Esther' : 'EST'}
    version_codes = dict(KJV=1, AMP=8, ESV=59, MSG=97, NET=107, NIV=111, NKJV=114)
    
    def __init__(self):
        pass
    
    def book_code(self, book):
        if book not in self.book_codes:
            raise Exception("Unrecognised bible book: "+str(book))
        return self.book_codes[book]
    
    def version_code(self, version):
        if version not in self.version_codes:
            raise Exception("Unrecognised bible version: "+str(version))
        return self.version_codes[version]
    
    def yves_file(self, version, book, chapter):
        book_dir = self.book_code(book)
        version_dir = str(self.version_code(version))
        filename = str(chapter)+".yves"
        chapter_path = os.path.join(self.yves_dir, version_dir, book_dir, filename)
        if not os.path.exists(chapter_path):
            raise Exception("Chapter file does not exist: "+chapter_path)
        return chapter_path

    def convert_byte(self, b):
        '''
        Decode yves-encoded byte.
        Maybe not the fastest way, but it's fast enough.
        '''
        s = '{:08b}'.format(b)
        new = s[3:]+s[:3]
        return int(new,2)
    
    def read_yves(self, filename):
        '''
        Read yves-encoded file, and return decoded text
        '''
        with open(filename, 'rb') as f:
            rawbuf = f.read()        
        buf = list(rawbuf)
        for f in range(0,len(buf),2):
            if f + 1 < len(buf):
                buf[f],buf[f+1] = self.convert_byte(buf[f+1]),self.convert_byte(buf[f])
        if len(buf) % 2 == 1:   # tidy up last byte of odd-length file
            buf[-1] = self.convert_byte(buf[-1])
        newstrbuf = bytes(buf).decode('utf-8')
        
        return newstrbuf

    def rst_nodes(self, options, version, book, chapter, verse = None, to_verse = None):
        fname = self.yves_file(version, book, chapter)
        rawxml = self.read_yves(fname)
        processor = ProcessYvesXML(rawxml)
        writer = RstWriter(options, verse,to_verse)
        nodes = processor.process(writer)
        #return writer.nodes
        return [writer.get_base_node()]
        #print(rawxml)
    
    
if __name__ == '__main__':
    print('test')
    y = YvesReader()
    nodes = y.rst_nodes({}, 'NET','Esther',9)
    print()
    print(nodes[-1].pformat())
    #for node in list(nodes[-1].traverse()):
    #    print(node)