#!/usr/bin/env python3

import sys
import textwrap

sys.path.append('../../pyth')

import verse_parser
from pyth.plugins.rtf15.reader import Rtf15Reader

import pyth

txt_width = 100

class Paragraph:
    
    def __init__(self):
        self.text = []
        self.props = []
        
    def __str__(self):
        s = ''
        for text,props in zip(self.text, self.props):
            if 'bold' in props:
                text = '*'+text+'*'
            if 'underline' in props:
                text = '_'+text+'_'
            # TODO: italics...
            s += text
        return s

class Book:
    
    def __init__(self, name):
        self.name = name
        
        self.introduction = None
        self.chapters = []
        
    def show(self):
        print(self.name)
        print()
        if self.introduction:
            self.introduction.show()
        for c in self.chapters:
            c.show()

class Introduction:
    
    def __init__(self):
        self.sub_intros = []
        self.doctrines = []
        
    def show(self):
        print("Introduction")
        for si in self.sub_intros:
            si.show()
        
class SubIntroduction:
    
    def __init__(self, name):
        self.name = name
        self.paragraphs = []
        
    def show(self):
        print("  "+self.name)
        for p in self.paragraphs:
            print(('\n').join(' '*4+line for line in textwrap.wrap(str(p), width=txt_width, subsequent_indent='  ')))

class Chapter():
    
    def __init__(self, name):
        self.name = name
        self.sections = []
        
    def show(self):
        print(self.name)
        for s in self.sections:
            s.show()
        
class Section():
    
    def __init__(self, name):
        self.name = name
        self.reference = None
        self.optional_introduction = []
        self.subsections = []
        self.application = []
        self.sidebars = [] # Like an application, but without the title "APPLICATION"
        self.doctrines = []
        
    def show(self):
        print('  [S]'+self.name)
        print('    [R]'+repr(self.reference))
        print('    Background and Analysis')
        if self.optional_introduction:
            for p in self.optional_introduction:
                print(('\n').join(' '*6+'[OI]'+line for line in textwrap.wrap(p, width=txt_width, subsequent_indent='  ')))
        for sub in self.subsections:
            sub.show()
        print('    Application')
        for p in self.application:
            print(('\n').join(' '*6+'[A]'+line for line in textwrap.wrap(p, width=txt_width, subsequent_indent='  ')))
        for s in self.sidebars:
            s.show()
        print('    Doctrines')
        for s in self.doctrines:
            print('      '+s)

class SideBar:
    
    def __init__(self, name):
        self.name = name
        self.paragraphs = []
        
    def show(self):
        print('    [SB]'+self.name)
        for p in self.paragraphs:
            print(('\n').join(' '*6+'[P]'+line for line in textwrap.wrap(str(p), width=txt_width, subsequent_indent='  ')))
        
        
class SubSection():

    
    def __init__(self, verse_ref):
        self.verse_ref = verse_ref
        self.paragraphs = []
        
        # The verse could be a verse range. We only know by either:
        # 1. subtracting one from the next verse
        # 2. If there is no next verse, the last verse should be the end of the eange for the section.
    
    def show(self):
        verse = self.verse_ref.split()[0]
        if verse in ('V','Verse'):
            verse = self.verse_ref.split()[1]
        print('    VERSE '+verse)
        for p in self.paragraphs:
            print(('\n').join(' '*6+'[V]'+line for line in textwrap.wrap(str(p), width=txt_width, subsequent_indent='  ')))
        
    
class ParseException(Exception):
    
    def __init__(self, text, props, msg):
        self.text = text
        self.props = props
        self.msg = msg
        
    def __str__(self):
        return 'text: "'+self.text+'" props: '+str(self.props)+' error: '+self.msg
       
class Reader:

    def __init__(self, fname, title):
        self.fname = fname
        self.title = title
        self.book = None

    def raw(self):
        self._readin_rtf()
        for text,props in zip(self.doc_text, self.doc_props):
            print(text,props)

    def read(self):
        self._readin_rtf()
        self.index = 0
        
        state = self._book
        while state:
            try:
                state = state()
            except StopIteration:
                break
        if state == None:
            print('Stopped at:',self.curr())
        return self.book

    def curr(self):
        return self.doc_text[self.index]
    
    def curr_props(self):
        return self.doc_props[self.index]
    
    def peek(self, offset=1):
        if self.index + offset >= len(self.doc_text):
            return "[EOF]"
        return self.text
    
    def is_all_caps(self, offset = 0):
        if self.index + offset >= len(self.doc_props):
            return False
        text = self.doc_text[self.index+offset]
        return text == text.upper()
    
    def is_paragraph_start(self, offset = 0):
        if self.index + offset >= len(self.doc_props):
            return False
        return len(self.doc_text[self.index+offset-1]) == 0
    
    def is_paragraph_end(self, offset = 0):
        if self.index + offset + 1 >= len(self.doc_props):
            return False
        return len(self.doc_text[self.index+offset+1]) == 0
    
    def is_plain(self, offset = 0):
        if self.index + offset >= len(self.doc_props):
            return False
        return len(self.doc_props[self.index + offset]) == 0
    
    def is_bold(self, offset = 0):
        if self.index + offset >= len(self.doc_props):
            return False
        return 'bold' in self.doc_props[self.index + offset]
    
    def is_bold_title(self, offset = 0):
        return self.is_all_caps() and self.is_bold() and self.is_paragraph_start() and self.is_paragraph_end()
    
    def is_underline(self, offset = 0):
        if self.index + offset >= len(self.doc_props):
            return False
        return 'underline' in self.doc_props[self.index + offset]
    
    def is_bold_underline(self, offset = 0):
        return self.is_bold() and self.is_underline()
    
    def __next__(self):
        
        self.index += 1
        if self.index >= len(self.doc_text):
            raise StopIteration()
        while self.doc_text[self.index] == '':
            self.index += 1
            if self.index >= len(self.doc_text):
                raise StopIteration()
            #print "end" # raise exception?
            #self.fail("end")

    def fail(self, reason):
        if self.index < len(self.doc_text):
            raise ParseException(self.curr(), self.doc_props[self.index], reason)
        raise ParseException("EOF","EOF",reason)

    def _book(self):
        print(self.curr().lower())
        while not self.is_bold_underline() or not self.curr().lower().startswith(self.title.lower()):
            next(self)
        self.book = Book(self.curr())
        next(self)
        return self._intro
    
    def _intro(self):
        self.book.introduction = Introduction()
        return self._sub_intro
    
    def _sub_intro(self):
        if not self.is_all_caps():
            self.fail("Expected subintro title to be all caps")
        if not self.is_plain():
            self.fail("Expected subintro title to not be bold or underline")
        si = SubIntroduction(self.curr())
        self.book.introduction.sub_intros.append(si)
        next(self)
        while not self.is_all_caps() and not self.curr().startswith("DOCTRINE"):
            if self.is_paragraph_start():
                si.paragraphs.append(Paragraph())
            si.paragraphs[-1].text.append(self.curr())
            si.paragraphs[-1].props.append(self.curr_props())
            next(self)
        if self.curr().startswith("DOCTRINE"):
            return self._doctrines
        if self.is_plain():
            return self._sub_intro
        # Could get bold-underline section heading if no doctrines?
        self.fail("Expected sub-intro title or DOCTRINES after subintro")
        
    def _doctrines(self):
        '''
        Currently, ignore all doctrines.
        After doctrines will be either a chapter or a section heading
        '''
        if not self.curr().startswith("DOCTRINE"):
            self.fail("Expected to find DOCTRINE(S) heading")
        next(self)
        while not self.is_bold_underline():
            if self.is_bold():
                if self.book.chapters:
                    self.book.chapters[-1].sections[-1].doctrines.append(self.curr())
                else:
                    self.book.introduction.doctrines.append(self.curr())
            next(self)
        if self.curr().startswith("CHAPTER"):
            print('Chapter:',self.curr())
            self.book.chapters.append(Chapter(self.curr()))
            next(self)
            if not self.is_bold_underline():
                self.fail("Expected heading after chapter to be bold underline")
        return self._section
    
    def _section(self):
        '''
        Title
        VerseRef
        Keywords
        BACKGROUND AND ANALYSIS
          optional introductory paragraphs
          bold verse(s)
          paragraphs
        APPLICATION
        DOCTRINE
        '''
        if not self.is_bold_underline():
            self.fail("Expected section heading to be bold and underline")
        sec = Section(self.curr())
        print("Section:",self.curr())
        next(self)
        self.book.chapters[-1].sections.append(sec)
        print("  Reference:",self.curr())
        verse_refs = verse_parser.Parser(self.curr()).parse_verse_references()
        if len(verse_refs) > 1:
            self.fail("Expected just one verse reference for section:"+self.curr())       
        sec.reference = verse_refs[0]
        next(self)
        while not self.curr().startswith('BACKGROUND'):
            next(self)
        next(self)
        
        #optional intro paragraphs
        while not self.is_verse() and not self.is_bold_title():
            sec.optional_introduction.append(self.curr())
            next(self)
        if self.curr().startswith('APPLICATION'):
            return self._application
        
        return self._subsection
    
    def is_verse(self):
        bits = self.curr().split()
        return self.is_bold() and \
               (bits[0].isdigit() or (bits[0] in ('V','Verse') and bits[1].isdigit())) and\
               self.is_paragraph_start() and self.is_paragraph_end()
        
    
    def _subsection(self):
        '''
        A bold paragraph is biblical text
        subsequent paragraphs are analyses of that text
        '''
        if not self.is_bold():
            self.fail("Expected biblical text in bold")
        if not self.is_verse():
            self.fail("Expected verse text to start with number or V number")
        ss = SubSection(self.curr())
        self.book.chapters[-1].sections[-1].subsections.append(ss)
        #print self.curr()
        next(self)
        while not (self.is_verse() or self.curr().startswith('APPLICATION')): #self.is_bold():
            if self.is_paragraph_start():
                ss.paragraphs.append(Paragraph())
            ss.paragraphs[-1].text.append(self.curr())
            ss.paragraphs[-1].props.append(self.curr_props())
            next(self)
        if self.curr().startswith('APPLICATION'):
            return self._application
        return self._subsection

    def _application(self):
        if not self.curr().startswith('APPLICATION') and not self.is_bold():
            self.fail("Expected bold APPLICATION here")
        next(self)
        while not self.is_bold_title():
            self.book.chapters[-1].sections[-1].application.append(self.curr())
            next(self)
        while self.is_bold_title() and not self.curr().startswith('DOCTRINE'):
            # A 'sidebar'. An extra non-doctrine note (e.g. in Luke 1 'Born in Bethlehem')
            sb = SideBar(self.curr())
            self.book.chapters[-1].sections[-1].sidebars.append(sb)
            #print self.curr()
            next(self)
            while not self.is_bold_title():
                #print self.curr()
                if self.is_paragraph_start():
                    sb.paragraphs.append(Paragraph())
                sb.paragraphs[-1].text.append(self.curr())
                sb.paragraphs[-1].props.append(self.curr_props())
                next(self)
        return self._doctrines

    def _readin_rtf(self):
        doc = Rtf15Reader.read(open(self.fname, 'r'))
    
        self.doc_text = []
        self.doc_props = []
        
        for i,element in enumerate(doc.content):
            if hasattr(element,"content"):
                if len(element.content) == 0:
                    self.doc_text.append('') # paragraph
                    self.doc_props.append([])
                for text in element.content:
                    if not isinstance(text, pyth.document.Text):
                        if isinstance(text, pyth.document.ListEntry):
                            continue
                        print("### Unknown paragraph element", text, file=sys.stderr)
                        sys.exit(1)
                    #print text.content[0]
                    self.doc_text.append(text.content[0])
                    self.doc_props.append(list(text.properties.keys()))
        self._formatting_fix_ups()
    
    def _formatting_fix_ups(self):
        '''
        Fix up formatting mistakes
        1. bold-text, non-bold space, bold-text   ->    bold-text
        '''
        i = 0
        while i < len(self.doc_text):
            if 'bold' in self.doc_props[i] and i <= len(self.doc_text) - 2:
                if self.doc_text[i+1].isspace() and 'bold' not in self.doc_props[i+1]:
                    if 'bold' in self.doc_props[i+2]:
                        self.doc_text[i] += self.doc_text[i+1] + self.doc_text[i+2]
                        del self.doc_text[i+1]
                        del self.doc_text[i+1]
                        del self.doc_props[i+1]
                        del self.doc_props[i+1]
            i += 1
        if len(self.doc_text) != len(self.doc_props):
            raise Exception("Formatting fix up broken")
                
        #print i,element
        
        
r = Reader(sys.argv[1], "gospel of luke")
book = r.read()
#book = r.raw()
if book:
    book.show()