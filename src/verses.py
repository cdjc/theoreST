#!/usr/bin/env python3
from tokenize import tokenize
import token
from io import BytesIO

class Token:
    
    def __eq__(self, o):
        return type(self) == type(o) and self.value == o.value
        
    def __str__(self):
        return self.value
        
    
class Book(Token):
    
    value = 'book'
    
    def __init__(self, name):
        self.value = name
        
class Number(Token):
    
    value = 'number'
    
    def __init__(self, name):
        self.value = name
        
    def __str__(self):
        return str(self.value)

class Colon(Token):
    
    value = ':'
    
class Comma(Token):
    
    value = ','
    
class Dash(Token):
    
    value = '-'
    
class Eof(Token):
     value = '<EOF>'
    
class Unknown(Token):
    def __init__(self, name):
        self.value = name

def to_bib_token(tok):
    
    tok_id, tok_val = tok
    if tok_id == token.NAME:
        return Book(tok_val)
    if tok_id == token.NUMBER:
        return Number(int(tok_val))
    if tok_id == token.OP:
        if tok_val == ':':
            return Colon()
        if tok_val == ',':
            return Comma()
        if tok_val == '-':
            return Dash()
    if tok_id == token.ENDMARKER:
        return Eof()
    return Unknown(tok_val)
    
def transform_for_numbered_books(toklist):
    '''
    transform token pairs in the list that form numbered books (1 John) into single book tokens
    '''
    rval = []
    maxi = len(toklist) - 2
    i = 0
    while i <= maxi:
        first = toklist[i]
        second = toklist[i + 1]
        if isinstance(first, Number) and isinstance(second,Book):
            if first.value in (1,2) and \
            second.value in ('Samuel', 'Kings','Chronicles','Corinthians','Thessalonians','Timothy','Peter') \
            or first.value in (1,2,3) and second.value == 'John':
                rval.append(Book(str(first.value)+' '+second.value))
                i += 2
                continue
        rval.append(first)
        i += 1
    rval.append(Eof())
    return rval
        
            

class ParseException(Exception):
    
    def __init__(self, expected, actual, parsed_so_far=[]):
        self.expected = expected
        if isinstance(self.expected, type):
            self.expected = {self.expected}
        self.actual = actual
    
    def __str__(self):
        return "Expected "+str([x.__name__ for x in self.expected])+" (actual "+str(self.actual)+")"

class Parser:
    
    def __init__(self, txt):
        self.tokens = transform_for_numbered_books([to_bib_token(x) for x in self.py_token_list(txt)])
        #print([x.value for x in self.tokens])
        #self.tokens = [to_bib_token(x) for x in self.py_token_list(txt)]
        #print(self.tokens)
        #print([x.value for x in self.tokens])
        unknowns = [x for x in self.tokens if type(x) == Unknown]
        #if len(unknowns) > 0:
        #    return Problem(
        self.index = 0
        self.refs = []
        self.book = None
        self.chapter = None
        self.text = ""
        self.swallowed = []
        
        
    def eof(self):
        return self.index >= len(self.tokens) or self.tokens[self.index] == Eof()
        
    def parse_verse_references(self):
        #print([x.value for x in self.tokens])
        
        state = self.p_book
        
        while state:
            state = state()
        
        if not self.cur_tok_is(Eof):
            raise ParseException({Eof},self.cur_tok())
        #print('now at:',self.cur_tok())
            
        return self.refs
        
    def p_book(self):
        self.book = self.swallow(Book)
        self.text += self.book.value
        return self.p_chapter
        
    def p_chapter(self):
        self.chapter = self.swallow(Number)
        self.text += ' '+str(self.chapter)
        if self.eof():
            self.refs.append(VerseReference(self.text, self.book, self.chapter, 1))
            self.text = ''
            return None
        if self.cur_tok_is(Comma):
            self.refs.append(VerseReference(self.text, self.book, self.chapter, 1))
            self.text = ''
            self.swallow()
            if self.cur_tok_is(Number):
                return self.p_chapter
            elif self.cur_tok_is(Book):
                return self.p_book
            raise ParseException({Number,Book},self.cur_tok())
        if self.cur_tok_is(Colon):
            self.swallow()
            self.text += ':'
            return self.p_verse
        raise ParseException({Comma,Colon,Eof},self.cur_tok())
        
    def p_verse(self):
        self.verse = self.swallow(Number)
        self.text += str(self.verse)
        self.to_verse = None
        self.range = False
        # range (5-17 or 6,7 where two adjacent numbers are separated by comma)
        if self.cur_tok_is(Dash) or self.cur_tok_is(Comma) and self.peek([Number]) and self.peek_ahead(1).value == self.verse.value + 1:
            self.swallow()
            self.to_verse = self.swallow(Number)
            self.text += '-'+str(self.to_verse)
            self.refs.append(VerseReference(self.text, self.book, self.chapter, self.verse, self.to_verse))
            self.text = ''
            self.range = True
        elif self.cur_tok_is(Eof):
            self.refs.append(VerseReference(self.text, self.book, self.chapter, self.verse,))
            self.text = ''
            return None
        if self.cur_tok_is(Eof):
            return None
            
        #print('here',self.cur_tok(),self.peek([Number]))
        if self.cur_tok_is(Comma):
            
            # another verse or a chapter or a book, (TODO: or a numbered book)
            if self.peek([Number,Colon]): # a chapter
                self.swallow(Comma)
                if not self.range:
                    self.refs.append(VerseReference(self.text, self.book, self.chapter, self.verse))
                    self.text = ''
                return self.p_chapter
            if self.peek([Book]): # a book
                self.swallow(Comma)
                if not self.range:
                    self.refs.append(VerseReference(self.text, self.book, self.chapter, self.verse))
                    self.text = ''
                return self.p_book
            if self.peek([Number]): # another verse
                self.swallow(Comma)
                if not self.range:
                    self.refs.append(VerseReference(self.text, self.book, self.chapter, self.verse))
                    self.text = ''
                return self.p_verse
            raise ParseException({Number,Book},self.cur_tok())
        raise ParseException({Dash,Comma,Eof},self.cur_tok())
        #if self.cur_tok_is(Eof):
        #    self.refs.append(VerseReference(self.text, self.book, self.chapter, self.verse, self.to_verse))
        #    return None
            
        
    def oob(self, index):
        return index >= len(self.tokens) 
        
    def peek(self,ls):
        for i,tok in enumerate(ls):
            peeki = self.index + i + 1
            if self.oob(peeki):
                return tok == Eof
            if type(self.tokens[peeki]) != tok:
                return False
        return True
        
    def cur_tok_is(self, tok):
        #print('cti',self.cur_tok(),tok)
        return type(self.cur_tok()) == tok
            
    def peek_ahead(self,number):
        if self.oob(self.index + number):
            return Eof()
        return self.tokens[self.index + number]
        
    def cur_tok(self):
        if self.oob(self.index):
            return Eof()
        return self.tokens[self.index]
        
    def swallow(self, tok = None):
        curtok = self.cur_tok()
        if tok == None or tok == type(curtok):
            self.swallowed.append(curtok)
            #print('swallow',curtok)
            self.index += 1
            return curtok
        raise ParseException(tok, self.cur_tok())
        
    def py_token_list(self, s):
        return [(x[0],x[1]) for x in tokenize(BytesIO(s.encode('ascii')).readline) if x[0] != 56]
    
class Problem:
    
    def __init__(self, expected, actual):
        self.expected = expected
        self.actual = actual
        
    def __eq__(self, o):
        return self.expected == o.expected and self.actual == o.actual
        
    def __str__(self):
        return "Expected "+expected+" but found "+actual
    
class VerseReference:
    
    def __init__(self, text, book, chapter, verse=None, to_verse=None):
        self.text = text.strip()
        self.book = book
        self.chapter = chapter
        self.verse = verse
        self.to_verse = to_verse
        
    def __eq__(self, o):
        return self.__repr__() == o.__repr__()
            
    def __repr__(self):
        s = '"'+self.text+'" '+str(self.book)+' '+str(self.chapter)
        if self.verse:
            s += ':'+str(self.verse)
            if self.to_verse:
                s += '-'+str(self.to_verse)
        return '('+s+')'
        
    
if __name__ == '__main__':
    tests = {'John 3:16' : [VerseReference('John 3:16', 'John', 3, 16)],
    'John 3,4' : [VerseReference('John 3', 'John', 3, 1), VerseReference('4', 'John', 4, 1)],
    'John John' : {Number},
    'John 3 Mark' : {Comma, Colon, Eof},
    'John 3:16-18' : [VerseReference('John 3:16-18', 'John', 3, 16, 18)],
    'John 3:16-18,21' : [VerseReference('John 3:16-18', 'John', 3, 16, 18), VerseReference('21', 'John', 3, 21)],
    'John 3' : [VerseReference('John 3', 'John', 3, 1)],
    'John 3:16,18' : [VerseReference('John 3:16', 'John', 3, 16), VerseReference('18', 'John', 3, 18)],
    'John 3:16,17' : [VerseReference('John 3:16-17', 'John', 3, 16,17)],
    'John 3, John 4' : [VerseReference('John 3', 'John', 3, 1), VerseReference('John 4', 'John', 4, 1)],
    'John 3:1, John 4' : [VerseReference('John 3:1', 'John', 3, 1), VerseReference('John 4', 'John', 4, 1)],
    'John 3, John 4:1' : [VerseReference('John 3', 'John', 3, 1), VerseReference('John 4:1', 'John', 4, 1)],
    'John 3:1-2,4-5,19,21-26' : [VerseReference('John 3:1-2', 'John', 3, 1, 2), 
                                VerseReference('4-5', 'John', 3, 4, 5),
                                VerseReference('19', 'John', 3, 19),
                                VerseReference('21-26', 'John', 3, 21,26)],
    'John 3:4-5,4:5-6' : [VerseReference('John 3:4-5', 'John', 3, 4, 5), VerseReference('4:5-6', 'John', 4, 5, 6)],
    '1 John 3:4,5,1 John 2:7' : [VerseReference('1 John 3:4-5', '1 John', 3, 4, 5),
                                VerseReference('1 John 2:7', '1 John', 2, 7)],
                                # TODO: more tests for errors.
    }

    def ref_list_as_str(verses):
        return ', '.join(x.text for x in verses)

    for txt in sorted(tests):
        print('-------------',txt)
        p = Parser(txt)
        try:
            vrlist = p.parse_verse_references()
        except ParseException as pe:
            state = 'failed'
            #print(tests[txt],pe.expected,tests[txt] == pe.expected)
            if tests[txt] == pe.expected:
                state = 'passed'
                print(txt, ' '*(25-len(txt)),'passed', pe)
            else:
                if isinstance(tests[txt], set):
                    print(txt, '\n\tfailed: expected exception expecting', [x.__name__ for x in tests[txt]])
                else:
                    print(txt, '\n\t','failed: expected:', tests[txt])
                print('\t','actual:',pe)
            continue
        if len(vrlist) != len(tests[txt]):
            print(txt,' failed: different length lists:')
            print('\texpected:\t',tests[txt])
            print('\tactual:  \t',vrlist)
            continue
        print('ref list:',ref_list_as_str(vrlist))
        for vr,expected in zip(vrlist,tests[txt]):
            if vr == expected:
                print(txt,' '*(25-len(txt)),'passed ',vr)
            else:
                print(txt,'\n\texpected:',expected,'\n\t  actual:',vr)
                
