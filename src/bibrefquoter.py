#!/usr/bin/env python3

# TODO: make unit tests, make modular, and rewrite. This code is pretty nasty

import sys
import collections
import re

names = ['1 Chronicles', '1 Corinthians', '1 John', '1 Kings', '1 Peter',
         '1 Samuel', '1 Thessalonians', '1 Timothy', '2 Chronicles', 
         '2 Corinthians', '2 John', '2 Kings', '2 Peter',
         '2 Samuel', '2 Thessalonians', '2 Timothy', '3 John',
         'Acts', 'Amos', 'Colossians', 'Daniel',
         'Deuteronomy', 'Ecclesiastes', 'Ephesians', 'Esther',
         'Exodus', 'Ezekiel', 'Ezra', 'Galatians',
         'Genesis', 'Habakkuk', 'Haggai', 'Hebrews',
         'Hosea', 'Isaiah', 'James', 'Jeremiah',
         'Job', 'Joel', 'John', 'Jonah',
         'Joshua', 'Jude', 'Judges', 'Lamentations',
         'Leviticus', 'Luke', 'Malachi', 'Mark',
         'Matthew', 'Micah', 'Nahum', 'Nehemiah',
         'Numbers', 'Obadiah', 'Philemon', 'Philippians',
         'Proverbs', 'Psalms', 'Psalm', 'Revelation', 'Romans',
         'Ruth', 'Song of Solomon', 'Song of Songs', 'Titus', 'Zechariah',
         'Zephaniah']

def bibquote(text):
    re_names = '('+'|'.join(names)+')'
    re2 = re_names+r'\s+\d+:(\s*(\d+|,|-|;|:|'+re_names+'))+'
        
    re1 = re.compile('('+re2+')')
    return re1.sub(r'`\1`', text)

def test():
    tests = \
    [(" sister (Acts 23:16), with"," sister (`Acts 23:16`), with"),
     (" sister Acts 23:16 with"," sister `Acts 23:16` with"),
     (" sister Acts 23:16,18 with"," sister `Acts 23:16,18` with"),
     (" sister Acts 23:16-18 with"," sister `Acts 23:16-18` with"),
     (" sister Acts 23:16, 18 with"," sister `Acts 23:16, 18` with"),
     (" sister Acts 23:16, 18:12 with"," sister `Acts 23:16, 18:12` with"),
     (" sister Acts 23:16, John 18:12 with"," sister `Acts 23:16, John 18:12` with"),
     ]
    
    for raw,expected in tests:
        if bibquote(raw) != expected:
            print('Fail:')
            print('raw:      ',raw)
            print('expected: ',expected)
            print('actual:   ',bibquote(raw))
        else:
            print('Pass:',expected)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        text = sys.stdin.read()
    
        print(bibquote(text))
    else:
        test()
          
                  