#!/usr/bin/env python3

def enum(**enums):
    return type('Enum', (), enums)
    
Versions = enum(ESV=1, KJV=2, NET=3)

def get_passage(version, book, chapter, verse, to_verse, format=''):
    pass

class Bible:
    
    def __init__(self, version):
        self.version = version
        
    
    
