#!/usr/bin/env python3
import sys

import options

import bible
import verse_parser

from docutils.parsers import rst
from docutils import statemachine

class BiblePassage(rst.Directive):
    required_arguments = 1
    optional_aguments = 0
    final_argument_whitespace = True

    def run(self):
        '''
        '''
        ref = self.arguments[0]
        print('****here',ref,options.bible,file=sys.stderr)
        vp = verse_parser.Parser(ref)
        try:
            vrefs = vp.parse_verse_references()
        except verse_parser.ParseException as pe:
            raise self.error("BiblePassage: parse verse ref error: "+str(pe))
        if len(vrefs) != 1:
            raise self.error("BiblePassage: One, and only one, verse reference allowed")
        vref = vrefs[0]
        
        

        rmtxt = '''Line1
Line2

And Line 3 '''+str(self.arguments)
        source = 'Bible Passage'
        include_lines = statemachine.string2lines(rmtxt, 0, convert_whitespace=True)
        self.state_machine.insert_input(include_lines, source)
        return []

rst.directives.register_directive('biblepassage', BiblePassage)
