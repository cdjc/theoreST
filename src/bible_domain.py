# -*- coding: utf-8 -*-
#python imports
import sys

#docutils imports
from docutils.parsers.rst import roles, Directive, directives
from docutils import nodes
from docutils import statemachine

#sphix imports
from sphinx.domains import Domain
from sphinx.roles import XRefRole
from sphinx.directives import ObjectDescription

#my imports
import bible
import verse_parser

import verse_role
from bibleyves import BiblePassageYVES

greek_role = roles.GenericRole('gk', nodes.emphasis)


    
class BiblePassage(Directive):
    required_arguments = 1
    optional_aguments = 0
    final_argument_whitespace = True
    version = None
    option_spec = {'bold':directives.flag}

    preamble = r'''

.. raw:: latex
    
    \begin{minipage}[c]{\textwidth}
    
'''
    
    postamble = r'''
    
.. raw:: latex
    
    \end{minipage} 
    
'''

    def run(self):
        '''
        '''
        env = self.state.document.settings.env
        #version = env.config.bible_version
        #print('options:',self.options, file=sys.stderr)
        if 'bible_version' not in env.config:
            raise self.error("BiblePassage: no bible version. Call set_version() after biblepassage import")
        ref = self.arguments[0]

        vp = verse_parser.Parser(ref)
        try:
            vrefs = vp.parse_verse_references()
        except verse_parser.ParseException as pe:
            raise self.error("BiblePassage: parse verse ref error: "+str(pe))
        if len(vrefs) != 1:
            raise self.error("BiblePassage: One, and only one, verse reference allowed")
        vref = vrefs[0]
        
        #verses = bible.
        #print(ref,'|',vref.book,'|',type(vref.book))
        
        verse = vref.verse.value if vref.verse else None
        to_verse = vref.to_verse.value if vref.to_verse else None

        rst = bible.get_passage_as_rst(env.config.bible_version, vref.book.value,
                                       vref.chapter.value, verse, to_verse,
                                       force=False)
        rst = self.preamble + rst + self.postamble
        #print(rst)
        source = 'Bible Passage'
        #include_lines = statemachine.string2lines(self.preamble, 0, convert_whitespace=False)
        #self.state_machine.insert_input(include_lines, source)
        include_lines = statemachine.string2lines(rst, 0, convert_whitespace=True)
        self.state_machine.insert_input(include_lines, source)
        #include_lines = statemachine.string2lines(self.postamble, 0, convert_whitespace=True)
        #self.state_machine.insert_input(include_lines, source)
        return []

class DraftComment(directives.body.Sidebar):
    
    def run(self):
        #print('DraftComment')
        env = self.state.document.settings.env
        if env.config.draft:
            #print('Draft!')
            return directives.body.Sidebar.run(self)
        else:
            #print('No draft...')
            return []

class BibleDomain(Domain):
    
    name = 'bible'
    label = 'Bible'
    
    object_types = {}
    
    directives = {'biblepassage' : BiblePassageYVES,
                  'draftcomment' : DraftComment}
    
    roles = {'gk' : greek_role,
             'verse' : verse_role.verse_reference_role}
    
    initial_data = {}
    
def setup(app):
    app.add_domain(BibleDomain)
    app.add_config_value('bible_version','NET', 'env')
    app.add_config_value('draft',False,'env')
    app.add_config_value('standalone',True,'env')
    