#!/usr/bin/env python3

import sys
import os
import pickle
import urllib.request
from bs4 import BeautifulSoup
import bs4
import re

module_dir = os.path.dirname(__file__)

def enum(**enums):
    return type('Enum', (), enums)
    
Version = enum(ESV='ESV', KJV='KJV', NET='NET')

loaded_bibles = {}


def get_passage_as_rst(version, book, chapter, verse=None, to_verse=None):
    verses = get_passage(version, book, chapter, verse, to_verse)
    

def get_passage(version, book, chapter, verse=None, to_verse=None, force=False):
    ensure_version_loaded(version)
    bible = loaded_bibles[version]
    return bible.get_verses(book, chapter, verse, to_verse, force)
    
def retrieve_verses(version, book, chapter):
    r = Retriever_BibleGateway('ESV')
    return r.get(book, chapter)

def ensure_version_loaded(version):

    if version in loaded_bibles:
        return
        
    filename = 'bible.'+version+'.pickle'
    path = os.path.join(module_dir, filename)

    if not os.path.exists(path):
        bible = Bible(version)
        loaded_bibles[version] = bible
        return

    with open(path, 'rb') as f:
        bible = pickle.load(f)
    loaded_bibles[version] = bible
    return
            
class BibleReferenceException(Exception):
    pass

class Bible:
    
    def __init__(self, version):
        self.version = version
        self.books = {}
        
    def get_verses(self, book, chapter, verse=None, to_verse=None, force=False):
        if book not in self.books:
            self.books[book] = Book(book, self)
        return self.books[book].get_verses(chapter, verse, to_verse, force)
        
    def save(self):
        base_file = 'bible.'+self.version+'.pickle'
        filename = base_file+'.new'
        path = os.path.join(module_dir, filename)
        
        with open(filename, 'wb') as f:
            pickle.dump(self, f, 3)
            
        os.rename(filename, base_file)
        
class Book:
    
    def __init__(self, name, bible):
        self.name = name
        self.bible = bible
        self.chapters = {}
        
    def get_verses(self, chapter, verse=None, to_verse=None, force=False):
        if chapter not in self.chapters:
            self.chapters[chapter] = Chapter(chapter, self)
        return self.chapters[chapter].get_verses(verse, to_verse, force)
        
    def __str__(self):
        return self.name
        
class Chapter:
    
    def __init__(self, number, book):
        self.number = number
        self.book = book
        self.verses = []
        
    def get_verses(self, verse_num, to_verse_num, force=False):
        if self.verses == [] or force:
            self.verses = retrieve_verses(self.book.bible.version, self.book, self)
            self.book.bible.save()
        if verse_num == None:
            return self.verses
        if to_verse_num == None:
            to_verse_num = verse_num
        rval = []
        # verse numbers might have a gap in them, so just do it the hard way
        for verse in self.verses:
            if verse.number >= verse_num and verse.number <= to_verse_num:
                rval.append(verse)
        return rval
        
    def __str__(self):
        return str(self.number)
    
class Verse:
    
    def __init__(self, number, lines, chapter=None):
        self.number = number
        self.lines = lines
        self.chapter = chapter
        self.footnotes = []
        
    def location(self):
        return (self.chapter.book.name+str(self.chapter.number)+'_'+str(self.number)).replace(' ','_')
        
    def __repr__(self):
        rval = str(self.number)+' '+'\n'.join(self.lines)
        if len(self.footnotes) > 0:
            rval += ' '+'{'+' | '.join(str(f) for f in self.footnotes)+'}'
        return rval
        
    def as_rest(self):
        pass
        
        
class Footnote:
    
    def __init__(self, text, ref, verse):
        self.text = text
        self.ref = ref
        self.verse = verse
        
    def __str__(self):
        return self.text
        
    def __repr__(self):
        return self.text

class Retriever_BibleGateway:
    
    def __init__(self, version):
        self.version = version
        
    def get(self, book, chapter):
        query = '?search='+str(book)+'%20'+str(chapter)+'&version='+self.version #+'&interface=print'
        query = query.replace(' ','%20').lower()
        
        url = 'http://www.biblegateway.com/passage/'+query
        print(url)
        #with urllib.request.urlopen(url) as getter:
        #    html = getter.read()
        #fname = 'tmp_'+str(book)+'_'+str(chapter)+'.html'
        #with open(fname, 'wb') as f:
        #    f.write(html)
        with open('p150.html', 'r') as f:
            html = f.read()
        soup = BeautifulSoup(html)
        
        #print(soup.prettify())
        verses = self.extract_verses(soup, chapter)
        return 
        footnotes = self.extract_raw_footnotes(soup)
        self.insert_footnotes_into_verses(verses,footnotes)

        return verses
    
    def extract_verses_old(self, soup, chapter):
        raw_verses = [x for x in soup.find_all('span') if x.has_key('class') and 'text' in x['class'] and x.text[0] in '123456789']

        # TODO: parse italics
        verse_text_ls = [x.text.split('\xa0') for x in raw_verses]
        # first verse is always verse 1, but number for first verse is chapter number
        verse_text_ls[0][0] = '1'
        
        return [Verse(int(x[0]),x[1], chapter) for x in verse_text_ls]
        
    def extract_verses(self, soup, chapter):
        head = [x for x in soup.find_all('div') if x.has_key('class') and 'passage' in x['class']][0]
        verses = []
        for child in head:
            if type(child) == bs4.element.NavigableString:
                continue
            if child.name.lower() in ['h1','h2','h3','h4','h5','h6']:
                continue
            if child.name == 'div' and child.has_key('class'):
                if 'footnotes' in child['class']:
                    break
                self.r_verses = []
                self.r_curr_verse_lines = []
                self.r_curr_verse_line = ''
                self.r_curr_verse_num = 0
                self.r_in_verse = False
                
                self.r_elem(child)
                
                self.r_curr_verse_lines.append(self.r_curr_verse_line)
                self.r_verses.append(Verse(self.r_curr_verse_num, self.r_curr_verse_lines))
                verses += self.r_verses
        for v in verses:
            print('----')
            print(v)
        return verses
        
    def r_elem(self, elem):
        if type(elem) == bs4.element.NavigableString:
            if self.r_in_verse:
                self.r_curr_verse_line += str(elem).strip()+' '
            return
        print('#',elem.name)
        if elem.name in ('div','p'):
            for child in elem.children:
                self.r_elem(child)
        elif elem.name == 'sup' and elem.has_key('class'):
            if 'versenum' in elem['class']:
                self.r_curr_verse_lines.append(self.r_curr_verse_line)
                self.r_verses.append(Verse(self.r_curr_verse_num, self.r_curr_verse_lines))
                
                self.r_curr_verse_num = int(elem.text)
                self.r_in_verse = True
                self.r_curr_verse_lines = []
                self.r_curr_verse_line = ''
            return
        elif elem.name == 'br':
            self.r_curr_verse_lines.append(self.r_curr_verse_line)
            self.r_curr_verse_line = ''
            return
        elif elem.name == 'span' and elem.has_key('class'):
            if 'chapternum' in elem['class']:
                self.r_curr_verse_num = 1
                self.r_in_verse = True
                self.r_curr_verse_lines = []
                self.r_curr_verse_line = ''
                return
            elif 'text' in elem['class']:
                for child in elem.children:
                    self.r_elem(child)
            elif 'small-caps' in elem['class']:
                self.r_curr_verse_line += elem.text.upper().strip()
            elif 'indent-1-breaks' in elem['class']:
                self.r_curr_verse_line += ''
            else:
                print('unknown class:',elem['class'])
                for child in elem.children:
                    self.r_elem(child)
                    
        elif elem.name == 'a':
            return
        else:
            print('unknown elem:',elem)
            
        
    def extract_raw_footnotes(self, soup):
        raw_footnote_parents = [x for x in soup.find_all('div') if x.has_key('class') and 'footnotes' in x['class']]
        raw_footnotes = raw_footnote_parents[0].find_all('li')
        footnotes = []
        for raw_footnote in raw_footnotes:
            rst = ''
            for raw_child in raw_footnote:
                #print(type(raw_child), hasattr(raw_child, 'name'))
                if not hasattr(raw_child,'name'):
                    rst += raw_child
                elif raw_child.name == 'i':
                    rst += '*'+raw_child.text+'*'
            footnotes.append(rst)
        return footnotes
        
    def insert_footnotes_into_verses(self, verse_list, raw_footnote_list):
        foot_i = 0
        for verse in verse_list:
            part_i = 1
            parts = re.split(r'\[\w\]',verse.text)
            text = parts[0]
            while part_i < len(parts):
                part = parts[part_i]
                ref = verse.location()+'_'+str(part_i)
                text += '[#'+ref+']' + part
                foot_text = raw_footnote_list[foot_i]
                verse.footnotes.append(Footnote(foot_text, ref, verse))
                foot_i += 1
                part_i += 1
                verse.text = text
            
get_passage('ESV', 'Psalm', 150, force=True)
