#!/usr/bin/env python3

'''
input:
  stdin: docbook xml of EBCWA commentary
  arg: start heading
'''

import sys, re

from bibrefquoter import bibquote 

para_re = re.compile(r'<para>(.*)</para>')

num_re = re.compile(r'([0-9]+)[.]\W+(.*)')
lett_re = re.compile(r'([a-z])[)]\W+(.*)')
rom_re = re.compile(r'((i+v?)|(vi*))[)]\W+(.*)')
ws_re = re.compile(r'^\W+$')

if len(sys.argv) not in (2,3):
    print("Usage: {0} heading".format(sys.argv[0]), file=sys.stderr)
    sys.exit(1)

heading = sys.argv[1]

if len(sys.argv) == 3:
    def finished(text):
        return text.startswith(sys.argv[2])
else:
    def finished(text):
        return text.upper() == text

matcher = '<para>'+heading+'</para>'

class Node:
    def __init__(self, level, text, numbered=True):
        self.level = level
        self.text = text.strip()
        self.children = []
        self.numbered = numbered
        

root = Node(0,'')
stack = [root]
stack_type = []

collecting = False

lines = sys.stdin.readlines()
last_match = ''
for line in lines:
    line = line.strip()
    #print(line)
    line = line.replace('\xa0','')
    if line == matcher:
        collecting = True
        print("Matching")
        continue
    #if 'CHARACTER' in line:
    #    print(line)
    #    print([(ord(c),c) for c in line])
    
    if not collecting:
        continue
    if line == "<para/>":
        continue
    match = para_re.match(line)
    if not match:
        continue
    text = match.group(1).strip()
    #print(text, file=sys.stderr)
    if text == '':
        continue

    if finished(text):
        print("Finish at "+text)
        break
    
    num_match = num_re.match(text)
    lett_match = lett_re.match(text)
    rom_match = rom_re.match(text)
    
    if lett_match and rom_match: # we have an 'i' or a 'v'
        if last_match[0] == 'let' and last_match[1] != 'h':
            lett_match = None
        if last_match[0] == 'rom':
            lett_match = None
                
    if num_match != None:
        #print("num ",num_match.group(1), num_match.group(2), file=sys.stderr)
        n = Node(1, num_match.group(2))
        root.children.append(n)
        last_match = ('num', num_match.group(1))
        continue
    if lett_match != None:
        #print("    let ",lett_match.group(1), lett_match.group(2), file=sys.stderr)
        n = Node(2, lett_match.group(2))
        root.children[-1].children.append(n)
        last_match = 'let',lett_match.group(1)
        continue
    if rom_match != None:
        #print("        rom ",rom_match.group(1), rom_match.group(4), file=sys.stderr)
        n = Node(3, rom_match.group(4))
        root.children[-1].children[-1].children.append(n)
        last_match = 'rom',rom_match.group(1)
        continue
    if (num_match, lett_match, rom_match) == (None, None, None):
        n = Node(-1,text,numbered = False)
        if len(root.children) > 0:
            root.children[-1].children.append(n) # Just fix this up manually later
        else:
            root.children.append(n)
        print("### ",text)

#end_of_ordered_list

def output_rest(node, depth, child_num = 0):
    prefix = ' ' * (3 * depth)
    
    if node.text:
        seq = '#'
        if child_num == 0:
            seq = '1ai1'[depth]
        print(prefix+seq+'.',bibquote(node.text), end='\n')
    if node.children:
        num_numbered_children = len([c for c in node.children if c.numbered])
        if num_numbered_children > 0:
            print()
            child_num = 0
            for child in node.children:
                if child.numbered:
                    output_rest(child, depth+1, child_num)
                    child_num += 1
        for child in node.children:
            if not child.numbered:
                print()
                print(prefix+'   '+bibquote(child.text), end='\n')
    print()


print(heading.capitalize())
print('~'*len(heading))
output_rest(root,-1)