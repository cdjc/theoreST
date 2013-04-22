#!/usr/bin/env python3

import sys
import os
import pickle
import urllib.request
from bs4 import BeautifulSoup

module_dir = os.path.dirname(__file__)

def enum(**enums):
    return type('Enum', (), enums)
    
Version = enum(ESV='ESV', KJV='KJV', NET='NET')

loaded_bibles = {}



def get_passage(version, book, chapter, verse, to_verse):
    ensure_version_loaded(version)
    bible = loaded_bibles[version]
    
def retrieve_verses(version, book, chapter):
    pass

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
        
    def get_verses(self, book, chapter, verse, to_verse):
        if book not in self.books:
            self.books[book] = Book(book, self)
        self.books[book].get_verses(chapter, verse, to_verse)
        
class Book:
    
    def __init__(self, name, bible):
        self.name = name
        self.bible = bible
        self.chapters = {}
        
    def get_verses(self, chapter, verse, to_verse):
        if chapter not in self.chapters:
            self.chapters[chapter] = Chapter(chapter, self)
        self.chapters[chapter].get_verses(verse, to_verse)
        
class Chapter:
    
    def __init__(self, number, book):
        self.number = number
        self.book = book
        self.verses = []
        
    def get_verses(self, verse, to_verse):
        if self.verses == []:
            self.verses = retrieve_verses(self.book.bible.version, self.book, self.number)
        if verse < 1 or verse > len(self.verses) or to_verse < 1 or to_verse > len(self.verses):
            raise BibleReferenceException('Verse out of range: '+self.book.bible.version+' '+\
            self.book+' '+str(self.number)+':'+str(verse)+'-'+str(to_verse)+' (actual:'+str(len(verses))+')')
        
    
class Verse:
    
    def __init__(self, number, parts):
        self.number = number
        self.parts # list of string and footnotes
        
class FootNote:
    
    def __init__(self, text):
        self.text = text

class Retriever_BibleGateway:
    
    def __init__(self, version):
        self.version = version
        
    def get(self, book, chapter):
        query = '?search='+book+'%20'+str(chapter)+'&version='+self.version #+'&interface=print'
        query = query.replace(' ','%20').lower()
        
        url = 'http://www.biblegateway.com/passage/'+query
        #with urllib.request.urlopen(url) as getter:
        #    html = getter.read()
        #with open('John1.html', 'wb') as f:
        #    f.write(html)
        with open('John1.html', 'r') as f:
            html = f.read()
        soup = BeautifulSoup(html)
        
        print(self.raw_verse_text_pairs(soup))
    
    def raw_verse_text_pairs(self, soup):
        raw_verses = [x for x in soup.find_all('span') if x.has_key('class') and 'text' in x['class'] and len(list(x.children)) > 1]
        #verse_pairs = {}
        #for rawv in raw_verses:
            #sup = rawv.find('sup')
            #if sup.has_key('class') and 'versenum' in sup['class']:
                #num = int(sup.text)
            #else:
                #num = 1 # first verse has no verse number, but chapter number instead
            #verse_pairs[num] = 
        verse_text_ls = [x.text.split('\xa0') for x in raw_verses]
        # firs verse is always verse 1, but number is chapter
        verse_text_ls[0][0] = '1'
        
        return [(int(x[0]),x[1]) for x in verse_text_ls]
        
    def raw_footnotes(self, soup):
        pass
        
r = Retriever_BibleGateway('ESV')
r.get('John',1)
