import os, sys

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
    options.books = set()
    
    books = sibling_folders()
    bible_versions = ['ESV','KJV']
    set_version = False
    for opt in ls:
        if opt in books:
            options.books.add(opt)
        elif opt in bible_versions:
            if set_version:
                print("Only one bible version allowed. Can see "+rval['bible_version']+' and '+opt)
                sys.exit(1)
            options.bible = opt
            set_version = True
        elif opt == 'draft':
            options.draft = True
            #print('DRAFT')
        else:
            print("Unknown option '"+opt+"'")
            sys.exit(1)
    if len(options.books) == 0:
        print("Must specify at least one book")
        sys.exit(1)
            
#TODO write some tests!

#print(sibling_folders())
#print(parse_options(sys.argv))