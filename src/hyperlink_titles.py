#!/usr/bin/env python3

import os

path = '../common'

for fname in os.listdir(path):
    if fname.endswith('.txt'):
        with open(os.path.join(path,fname),'r') as f:
            print('`'+f.readline().strip()+'`_')