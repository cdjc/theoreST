import os, sys
import glob

base_dir = '..'
book_dirs = ['nt_commentary/*','doctrines']

def get_books():
    dirs = []
    for pattern in (os.path.join(base_dir,x) for x in book_dirs):
        dirs += [x for x in glob.glob(pattern) if os.path.isdir(x)]
    
    rval = {}
    for d in dirs:
        rval[os.path.basename(d)] = d
    #print(rval)
    return rval

def sibling_folders(exclude = ['common','src']):
    folders = []
    sibling_files = os.listdir('..')
    for name in sibling_files:
        if name in exclude or name.startswith('.'):
            continue
        path = os.path.join('..',name)
        if os.path.isdir(path):
            folders.append(name)
    return folders

def parse_options(options, ls):
    options.books = {}
    
    books = get_books()
    bible_versions = ['ESV','KJV']
    set_version = False
    for opt in ls:
        if opt in books:
            options.books[opt] = books[opt]
        elif opt in bible_versions:
            if set_version:
                print("Only one bible version allowed. Can see "+rval['bible_version']+' and '+opt)
                sys.exit(1)
            options.conf_overrides['bible_version'] = opt
            set_version = True
        elif opt == 'draft':
            options.conf_overrides['draft'] = True
            #print('DRAFT')
        elif opt == 'force':
            options.force = True
        else:
            print("Unknown option '"+opt+"'")
            sys.exit(1)
    #if len(options.books) == 0:
    #    print("Must specify at least one book")
    #    sys.exit(1)
            
#TODO write some tests!

#print(sibling_folders())
#print(parse_options(sys.argv))