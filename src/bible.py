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


def get_passage_as_rst(version, book, chapter, verse=None, to_verse=None, force=False):
    ensure_version_loaded(version)
    verses = get_passage(version, book, chapter, verse, to_verse, force)
    return verses_as_rest(verses)

def get_passage(version, book, chapter, verse=None, to_verse=None, force=False):
    ensure_version_loaded(version)
    bible = loaded_bibles[version]
    return bible.get_verses(book, chapter, verse, to_verse, force)
    
def retrieve_verses(version, book, chapter):
    r = Retriever_BibleGateway(version)
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
        path_new = os.path.join(module_dir, filename)
        path = os.path.join(module_dir, base_file)
        print('svae_path:',path)
        
        with open(path_new, 'wb') as f:
            pickle.dump(self, f, 3)
            
        os.rename(path_new, path)
        
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
        rval = str(self.lines)
        #rval = str(self.number)+'\n'+'\n'.join((''.join(y[1] for y in x) for x in self.lines))
        if len(self.footnotes) > 0:
            rval += ' '+'{'+' | '.join(str(f) for f in self.footnotes)+'}'
        return rval
        

def verses_as_rest(verses):
    rval = ''
    prefix = ' |'
    for verse in verses:
        done_num = False
        numtxt = str(verse.number)
        if numtxt == '0':
            numtxt = ''
        for line in verse.lines:
            seen_poetry = False
            for tag,text in line:
                if tag == 'p':
                    rval += '\n'+prefix
                    continue
                if tag == 'poetry' and not seen_poetry:
                    rval += '\n'+prefix
                    if done_num:
                        rval += '     '
                    else:
                        rval += ' ' + numtxt + ' '*(4-len(numtxt))
                        done_num = True
                    seen_poetry = True
                if not done_num:
                    rval += ' '+numtxt+' '
                    done_num = True
                rval += text
    seen_footnotes = False
    for verse in verses:
        footnote_idx = 1
        for footnote in verse.footnotes:
            if not seen_footnotes:
                rval += '\n'#+prefix
            rval += '\n'#+prefix
            raw_ref = verse.location()+'_'+str(footnote_idx)
            footnote_idx += 1
            rval += '.. '+'[#'+raw_ref+']'+footnote.text+'\n'
    rval += '\n\n'
    return rval
        
        
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
        with urllib.request.urlopen(url) as getter:
            html = getter.read()
        fname = 'tmp_'+str(book)+'_'+str(chapter)+'.html'
        path = os.path.join(module_dir, fname)
        with open(path, 'wb') as f:
            f.write(html)
        #with open('tmp_Ecclesiastes_3.html', 'r') as f:
        #    html = f.read()
        soup = BeautifulSoup(html)
        
        verses = self.extract_verses(soup, chapter)

        footnotes = self.extract_raw_footnotes(soup)
        self.insert_footnotes_into_verses(verses,footnotes)

        return verses
    
    def extract_verses(self, soup, chapter):
        head = [x for x in soup.find_all('div') if x.has_key('class') and 'passage' in x['class']][0]
        verses = []
        for child in head:
            if type(child) == bs4.element.NavigableString:
                continue
            if child.name.lower() in ['h1','h2','h3','h4','h5','h6']:
                if child.has_key('class') and 'psalm-title' in child['class']:
                    self.r_curr_verse_num = 0
                    self.r_verses = []
                    self.r_curr_verse_lines = []
                    self.r_curr_verse_line = []
                    self.r_is_p = True
                    self.r_elem(child)
                    
                    if self.r_curr_verse_line:
                        self.r_curr_verse_lines.append(self.r_curr_verse_line)
                        self.r_verses.append(Verse(self.r_curr_verse_num, self.r_curr_verse_lines))
                        verses += self.r_verses
                
            if child.name == 'div' and child.has_key('class') or child.name == 'p':
                if child.name == 'div' and 'footnotes' in child['class']:
                    break
                self.r_text_type = 'plain'
                if child.name == 'div' and 'poetry' in child['class']:
                    self.r_text_type = 'poetry'
                self.r_verses = []
                self.r_curr_verse_lines = []
                self.r_curr_verse_line = []
                self.r_is_p = False # Will get set to true if child.name == 'p'
                self.r_curr_verse_num = -1 # 0 is for psalm-titles
                
                self.r_elem(child)
                
                self.r_add_verse()

                verses += self.r_verses
        #for v in verses:
        #    print('----')
        #    print(v)
        #print(verses_as_rest(verses))
        for verse in verses:
            verse.chapter = chapter
        return verses

    def r_add_verse(self):
        if self.r_curr_verse_line:
            self.r_curr_verse_lines.append(self.r_curr_verse_line)
        if self.r_curr_verse_num != -1:
            if self.r_is_p:
                self.r_curr_verse_lines[0].insert(0,('p',''))
                self.r_is_p = False
            self.r_verses.append(Verse(self.r_curr_verse_num, self.r_curr_verse_lines))
        
    def r_elem(self, elem):
        if type(elem) == bs4.element.NavigableString:
            if str(elem).strip():
                self.r_curr_verse_line.append((self.r_text_type,str(elem)))
            return
        #print('#',elem.name)
        if elem.name in ('div','p'):
            if elem.name == 'p':
                self.r_is_p = True
            for child in elem.children:
                self.r_elem(child)
        elif elem.name == 'sup' and elem.has_key('class'):
            if 'versenum' in elem['class']:
                self.r_add_verse()
                
                self.r_curr_verse_num = int(elem.text)
                self.r_in_verse = True
                self.r_curr_verse_lines = []
                self.r_curr_verse_line = []
            elif 'footnote' in elem['class']:
                self.r_curr_verse_line.append(('fn','[F]'))
            return
        elif elem.name == 'br':
            self.r_curr_verse_lines.append(self.r_curr_verse_line)
            self.r_curr_verse_line = []
            return
        elif elem.name == 'span' and elem.has_key('class'):
            if 'chapternum' in elem['class']:
                self.r_curr_verse_num = 1
                self.r_in_verse = True
                self.r_curr_verse_lines = []
                self.r_curr_verse_line = []
                return
            elif 'text' in elem['class']:
                for child in elem.children:
                    self.r_elem(child)
            elif 'small-caps' in elem['class']:
                self.r_curr_verse_line.append(('sc',elem.text))
            elif 'indent-1-breaks' in elem['class']:
                self.r_curr_verse_line.append(('tab','    '))
                pass #self.r_curr_verse_line += ''
            else:
                print('unknown class:',elem['class'])
                for child in elem.children:
                    self.r_elem(child)
                    
        elif elem.name == 'a':
            self.r_curr_verse_line.append(('a',elem.text.strip()))
            return
        else:
            for child in elem.children:
                self.r_elem(child)
            #print('unknown elem:',elem)
            
        
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
            for line in verse.lines:
                for idx,pair in enumerate(line):
                    if pair[0] == 'fn':
                        ref = ' [#'+verse.location()+'_'+str(part_i)+']_'
                        line[idx] = ('fn',ref)
                        foot_text = raw_footnote_list[foot_i]
                        verse.footnotes.append(Footnote(foot_text, ref, verse))
                        foot_i += 1
                        part_i += 1
