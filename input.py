
size = int(input("Size (or sudoku)?"))

blocks = []
cells = []

if size == 'sudoku':
    print "Awaiting sudoku set values..."
    
    while True:
        b = []
        v = raw_input("Value?")
        if v == "": break
        b.append("%s=" % (v,))
        c_str = raw_input("Cell?")
        if c_str == "": break
        c = tuple(int(i) for i in c_str.split(','))
        if c in cells:
            print "WTF?"
            continue
        b.append(c)
        cells.append(c)
        blocks.append(b)
else:
    print "Awaiting mathdoku conditions and blocks..."
    
    max_cells = size**2

    while len(cells)<max_cells:
        b = []
        blocks.append(b)
        cond = raw_input("Condition?")
        b.append(cond)
        while True:
            c_str = raw_input("Cell?")
            if c_str == "": break
            c = tuple(int(i) for i in c_str.split(','))
            if c in cells:
                print "WTF?"
                continue
            b.append(c)
            cells.append(c)

name = raw_input("Name?")

print """add(%s, %s,
*%s)""" % (repr(name), repr(size), repr(blocks))
