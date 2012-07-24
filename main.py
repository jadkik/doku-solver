from collections import defaultdict

DO_LOG = False
def log(level, *args):
    if not DO_LOG: return
    print "  "*level, " ".join(str(a) for a in args)

class Grid(object):
    def __init__(self, size):
        if size == 'sudoku':
            self.size = 9
            self.sudoku = True
        else:
            self.size = size
            self.sudoku = False
        self.nums = tuple(range(1, self.size+1))
        self.cells = {(x, y): Cell(self, x, y) for x in range(self.size) for y in range(self.size)}
        self.groups = []
        self.removed_groups = []
        
        self.__setup = False
    
    def add_group(self, grp):
        if not self.__setup:
            self.groups.append(grp)
    
    def remove_group(self, grp):
        self.groups.remove(grp)
        self.removed_groups.append(grp)
    
    def group_merge(self, group):
        if any(grp == group for grp in self.groups):
            log(0, "**", "I won't add", group)
        else:
            log(0, "**", "Adding", group)
            self.groups.append(group)
    
    def at(self, x, y):
        return self.cells[x, y]
    
    def row(self, y):
        return [self.at(x, y) for x in range(self.size)]
    
    def column(self, x):
        return [self.at(x, y) for y in range(self.size)]
    
    def set(self, x, y, value):
        self.at(x, y).set_value(value)
    
    def setup(self):
        
        if self.sudoku:
            blks = {}
            for x in range(3):
                for y in range(3):
                    blks[x,y] = b = Block(self)
                    b.set(UniqueCondition(self.nums))
            
            for x in range(self.size):
                for y in range(self.size):
                    blks[int(x/3), int(y/3)].add(self.at(x,y))
        
        for c in self:
            assert c.has_block(), "The cell at position (%d,%d) that does not have a block!" % (c.x, c.y)
        
        [Row(self, i) for i in range(self.size)]
        [Column(self, i) for i in range(self.size)]
        
        conds = (EqualityCondition, UniqueCondition, ProductCondition,
                SumCondition, DivisionCondition, DifferenceCondition)
        self.sort_conds = {cond: i for i, cond in enumerate(conds)}
        
        self.__setup = True
    
    def validate(self):
        for grp in self.groups:
            if not grp.validate():
                return False
        else:
            return True
    
    def process(self):
        self.update_group_inclusions()
        self.process_groups()
        
    def update_group_inclusions(self):
        grp_cells = [(grp, set(grp.cells)) for grp in self.groups]
        for i, (grp1, cells1) in enumerate(grp_cells):
            for grp2, cells2 in grp_cells[i+1:]:
                if cells1.issubset(cells2):
                    grp2.set_includes(grp1)
                elif cells2.issubset(cells1):
                    grp1.set_includes(grp2)
    
    def process_groups(self):
        self.groups.sort(key=self.sort_groups)
        
        for grp in self.groups[:]:
            grp.process()
    
    def sort_groups(self, grp):
        return (self.sort_conds[grp.condition.__class__],
                len(grp),
                min(grp.cells))
    
    def display(self, only_numbers=True):
        if only_numbers:
            for y in range(self.size):
                for c in self.row(y):
                    print c.value if c.value is not None else '_',
                print
        else:
            grp_info = defaultdict(str)
            for grp in self.groups:
                if not isinstance(grp, Block): continue
                min_cell = min(grp.cells)
                cond_txt = grp.condition.symbol()
                grp_info[min_cell] = cond_txt
            
            for y in range(self.size):
                print "|",
                for c in self.row(y):
                    print "%3s %s|" % (grp_info[c], c.value if c.value is not None else '_'),
                print 
                print "_"*(1+7*self.size)
    
    def __iter__(self):
        return self.cells.itervalues()

class Cell(object):
    def __init__(self, grid, x, y):
        self.grid = grid
        self.x, self.y = x, y
        self.block = None
        self.groups = []
        
        self.__value = None
        self.__possible_values = set(self.grid.nums)
    
    @property
    def value(self):
        return self.__value
    
    @value.setter
    def value(self, v):
        log(0, "*"*5, self, "=", v, "?")
        self.__value = v
        if v is not None:
            self.update_value()
    
    def has_value(self):
        return self.value is not None
    
    def update_value(self):
        L = len(self.possible)
        assert L > 0, "No possible value for %s?" % (self,)
        if self.value is None and L == 1:
            self.__value = list(self.possible)[0]
            log(0, "*"*10, self, "=", self.__value, "!")
        elif self.value is not None and L > 1:
            self.__possible_values = set([self.value])
    
    @property
    def possible(self):
        return self.__possible_values
    
    @possible.setter
    def possible(self, values):
        if values is None:
            values = self.grid.nums
        self.__possible_values = set(values)
        self.update_value()
    
    def restrict(self, v):
        if type(v) == int:
            self.possible.discard(v)
        else:
            self.possible.difference_update(set(v))
        self.update_value()
    
    def allow(self, v):
        if type(v) == int:
            self.possible.add(v)
        else:
            self.possible.update(set(v))
        self.update_value()
    
    def add_group(self, grp):
        self.groups.append(grp)
    
    def set_block(self, block):
        self.block = block
    
    def has_block(self):
        return self.block is not None
    
    def __lt__(self, c):
        return (self.y, self.x) < (c.y, c.x)
    
    def __repr__(self):
        return "c(%d,%d)" % (self.x, self.y)

class Group(object):
    def __init__(self, grid):
        self.grid = grid
        self.cells = [] # order is important! (even though there should not be duplicates)
        self.condition = None
        
        self.certain_values = set([])
        self.included_groups = set([])
        
        self.info = None
        
        self.is_attached = False
        self.attach()
    
    def attach(self):
        self.grid.add_group(self)
        self.is_attached = True
    
    def detach(self):
        self.grid.remove_group(self)
        self.is_attached = False
    
    def add(self, cell):
        assert cell not in self.cells, "Cell %s is already in group %s!" % (cell, group)
        self.cells.append(cell)
        cell.add_group(self)
    
    def set(self, condition):
        self.condition = condition
        self.condition.assign(self)
    
    def restrict(self, value):
        [c.restrict(value) for c in self]
    
    def allow(self, value):
        [c.allow(value) for c in self]
    
    def certain(self, values):
        self.certain_values = set(values)
        if len(self.certain_values) == len(self):
            for c in self:
                c.possible.intersection_update(values)
    
    def set_includes(self, group):
        self.included_groups.add(group)
    
    def includes(self, group):
        return group in self.included_groups
    
    def validate(self):
        return self.condition.validate()
    
    def process(self):
        log(0, "#", "Processing", self)
        self.condition.process()
    
    def __getitem__(self, i):
        return self.cells[i]
    
    def __iter__(self):
        return iter(self.cells)
    
    def __len__(self):
        return len(self.cells)
    
    def __eq__(self, grp):
        return set(grp.cells) == set(self.cells) and \
                self.condition == grp.condition
    
    def __lt__(self, grp):
        return min(self.cells) < min(grp.cells)
    
    def __repr__(self):
        return "G(c%d, %s, %s)" % (len(self), self.condition, self.cells)

class Block(Group):
    def __init__(self, grid):
        super(Block, self).__init__(grid)
    
    def add(self, cell):
        assert not cell.has_block(), "In %s: Cell %s has a block already (%s)!" % (self, cell, cell.block)
        super(Block, self).add(cell)
        cell.set_block(self)
    
    def __repr__(self):
        return "B(c%d, %s)" % (len(self), self.condition)

class Row(Group):
    def __init__(self, grid, y):
        super(Row, self).__init__(grid)
        
        self.y = y
        
        self.set(UniqueCondition(list(self.grid.nums)))
        [self.add(c) for c in self.grid.row(self.y)]
    
    def __repr__(self):
        return "R(c%d, (x, %d))" % (len(self), self.y)

class Column(Group):
    def __init__(self, grid, x):
        super(Column, self).__init__(grid)
        
        self.x = x
        
        self.set(UniqueCondition(list(self.grid.nums)))
        [self.add(c) for c in self.grid.column(self.x)]
    
    def __repr__(self):
        return "C(c%d, (%d, y))" % (len(self), self.x)

class Condition(object):
    def __init__(self, value):
        self.value = value
        self.group = None
        self.grid = None
    
    def assign(self, group):
        self.group = group
        self.grid = self.group.grid
    
    def validate(self):
        return False
    
    def filter_solutions(self, grp, sols):
        pass
    
    def process(self):
        pass
    
    def get_filtered_solutions(self, sols):
        groups = set()
        for c in self.group:
            groups.update(set(c.groups))
        
        sols = sols.copy()
        for grp in groups:
            if not isinstance(grp.condition, UniqueCondition): continue
            sols = grp.condition.filter_solutions(self.group, sols)
        
        return sols
    
    def __eq__(self, cond):
        return type(self) == type(cond) and self.value == cond.value
    
    def symbol(self):
        return "?%s" % (self.value,)
    
    def __repr__(self):
        return "/%s(%s)" % (self.__class__.__name__[:-9], self.value)

class UniqueCondition(Condition):
    # TODO: split ExactCondition  (contain exactly all values in self.value)
    #         and UniqueCondition (contain at most one value of self.value)
    # The idea is still not clear, I'll check that
    
    def __init__(self, value):
        super(UniqueCondition, self).__init__(set(value))
    
    def validate(self):
        values = [c.value for c in self.group]
        counts = {v: values.count(v) for v in values}
        try:
            for v in self.value:
                if counts[v] != 1:
                    return False
        except KeyError:
            return False
        else:
            return True

    def filter_solutions(self, grp, sols):
        sols = sols.copy()
        cell_indices = [i for i, c in enumerate(grp) if c in self.group.cells]
        
        for s in sols.copy():
            values = [s[i] for i in cell_indices]
            for v in self.value:
                if values.count(v) > 1:
                    sols.remove(s)
                    break
        
        return sols

    def process(self):
        self.group.certain(self.value)
        
        remaining_values = set(self.value)
        remaining_cells = set(self.group.cells)
        for grp in self.group.included_groups:
            if len(grp.certain_values) > 0:
                remaining_values -= set(grp.certain_values)
                remaining_cells -= set(grp.cells)
        
        taken_values = set(self.value)-remaining_values
        for c in remaining_cells:
            c.restrict(taken_values)
        
        if self.desintegrate():
            return
        
        self.info = [remaining_cells, remaining_values]
        
    
    def desintegrate(self):
        remaining_values = set(self.value)
        remaining_cells = set(self.group.cells)
        
        for c in self.group:
            if c.value is not None:
                remaining_cells.discard(c)
                remaining_values.discard(c.value)
        
        taken_values = set(self.value)-remaining_values
        for c in remaining_cells:
            c.restrict(taken_values)
        
        if len(remaining_cells) == 0:
            self.group.detach()
        elif len(remaining_cells) == len(self.group):
            pass
        elif len(remaining_cells) == 1:
            r = list(remaining_cells)
            print r[0], "=", r[0].value
        else:
            grp = Group(self.grid)
            [grp.add(c) for c in remaining_cells]
            grp.set(UniqueCondition(remaining_values))
            self.grid.group_merge(grp)
        
            self.group.detach()
    
    def symbol(self):
        return ""

class EqualityCondition(Condition):
    def validate(self):
        assert len(self.group) == 1, "EqualityCondition only works with one-cell groups (%d cells here)!" % (len(self.group),)
        
        return self.group[0].value == self.value

    def process(self):
        self.group[0].value = self.value
        
        log(1, self.group[0], "=", self.value)
        
        self.group.detach()
    
    def symbol(self):
        return str(self.value)

class SumCondition(Condition):
    def validate(self):
        assert len(self.group) > 1, "SumCondition only works with 2 or more cells (%d cells here)!" % (len(self.group),)
        try:
            s = sum(c.value for c in self.group)
        except TypeError:
            return False
        return (s == self.value)

    def process(self):
        # if a value is bigger than the total sum, discard it
        self.group.restrict(v for v in self.grid.nums if v>self.value)
        
        if self.desintegrate():
            log(0, "** Group", self, "was desintegrated. Done here.")
            return
        
        sols = self.solve(self.value, [c.possible for c in self.group])
        # set to only keep unique items, and tuple to be able to put them in a set
        sols = set(tuple(s) for s in sols)
        
        log(0, 'SOLUTIONS for sum =', self.value)
        log(1, sols)
        
        filtered_sols = self.get_filtered_solutions(sols)
        
        if sols == filtered_sols:
            log(1, "FILTERED SOLUTIONS did not change anything")
            
            self.group.info = sols
        else:
            log(0, 'In >', self.group.cells)
            log(0, 'FILTERED SOLUTIONS')
            log(1, filtered_sols)
        
            self.group.info = (sols, filtered_sols)
        
            sols = filtered_sols

        # Values that are in every possibility of the group
        certain_values = [v for v in self.grid.nums if all(v in poss for poss in sols)]
        log(1, 'certain values:', certain_values)
        self.group.certain(certain_values)
        
        for i, c in enumerate(self.group):
            c.possible = set(s[i] for s in sols)
        
        self.desintegrate()
    
    def solve(self, total, all_poss, level=0):
        all_poss = [poss.copy() for poss in all_poss]
        count = len(all_poss)
        
        if count == 0 and total == 0:
            return [[]]
        elif count == 0:
            return None
        elif any(len(poss) == 0 for poss in all_poss):
            return None
        
        restricted = set(v for v in self.grid.nums if v>total)
        for poss in all_poss:
            poss.difference_update(restricted)
        
        results = []
        #log(level, "solve(", total, count, all_poss, ")")
        
        for i, cell_poss in enumerate(all_poss):
            left_poss = all_poss[:i]+all_poss[i+1:]
            #log(level, "now cell", i, all_poss, '->', left_poss)
            for v in cell_poss:
                #log(level, v, "plus")
                assert total>=v, "Oops! The value %d was not eliminated for total %d" % (v, total)
                sols = self.solve(total-v, left_poss, level=level+1)
                if sols is None: continue
                for p in sols:
                    p.insert(i, v)
                    results.append(p)
        return results
    
    def desintegrate(self):
        remaining_cells = []
        remaining_total = self.value
        
        for c in self.group:
            if c.value is None:
                remaining_cells.append(c)
            else:
                remaining_total -= c.value
        
        if len(remaining_cells) == 0:
            self.group.detach()
            return True
        elif len(remaining_cells) == len(self.group):
            return False
        elif len(remaining_cells) == 1:
            return False # TODO: should it?
        else:
            grp = Group(self.grid)
            [grp.add(c) for c in remaining_cells]
            grp.set(SumCondition(remaining_total))
            self.grid.group_merge(grp)
            
            self.group.detach()
            return True
    
    def symbol(self):
        return "%s+" % (self.value,)

class ProductCondition(Condition):
    def validate(self):
        try:
            p = 1
            for c in self.group:
                p *= c.value
        except TypeError:
            return False
        return (p == self.value)

    def process(self):
        # if a value is bigger than the total product or is not a divisor of it, discard it
        self.group.restrict(v for v in self.grid.nums if v>self.value or \
                                                            self.value%v != 0)
        
        if self.desintegrate():
            log(0, "** Group", self, "was desintegrated. Done here.")
            return
        
        sols = self.solve(self.value, [c.possible for c in self.group])
        # set to only keep unique items, and tuple to be able to put them in a set
        sols = set(tuple(s) for s in sols)
        
        log(0, 'SOLUTIONS for product =', self.value)
        log(1, sols)
        
        filtered_sols = self.get_filtered_solutions(sols)
        
        if sols == filtered_sols:
            log(1, "FILTERED SOLUTIONS did not change anything")
            
            self.group.info = sols
        else:
            log(0, 'In >', self.group.cells)
            log(0, 'FILTERED SOLUTIONS')
            log(1, filtered_sols)
        
            self.group.info = (sols, filtered_sols)
        
            sols = filtered_sols

        # Values that are in every possibility of the group
        certain_values = [v for v in self.grid.nums if all(v in poss for poss in sols)]
        log(1, 'certain values:', certain_values)
        self.group.certain(certain_values)
        
        for i, c in enumerate(self.group):
            c.possible = set(s[i] for s in sols)
        
        self.desintegrate()
    
    def solve(self, total, all_poss, level=0):
        all_poss = [poss.copy() for poss in all_poss]
        count = len(all_poss)
        
        if count == 0 and total == 1:
            return [[]]
        elif count == 0:
            return None
        elif any(len(poss) == 0 for poss in all_poss):
            return None
        
        restricted = set(v for v in self.grid.nums if v>total or total%v != 0)
        for poss in all_poss:
            poss.difference_update(restricted)
        
        results = []
        log(level, "solve(", total, count, all_poss, ")")
        
        for i, cell_poss in enumerate(all_poss):
            left_poss = all_poss[:i]+all_poss[i+1:]
            log(level, "now cell", i, all_poss, '->', left_poss)
            for v in cell_poss:
                log(level, v, "times")
                assert total>=v and total%v == 0, "Oops! The value %d was not eliminated for total %d" % (v, total)
                sols = self.solve(total/v, left_poss, level=level+1)
                if sols is None: continue
                for p in sols:
                    p.insert(i, v)
                    results.append(p)
        return results
    
    def desintegrate(self):
        remaining_cells = []
        remaining_total = self.value
        
        for c in self.group:
            if c.value is None:
                remaining_cells.append(c)
            else:
                remaining_total /= c.value
        
        if len(remaining_cells) == 0:
            self.group.detach()
            return True
        elif len(remaining_cells) == len(self.group):
            return False
        elif len(remaining_cells) == 1:
            return False # TODO: should it?
        else:
            grp = Group(self.grid)
            [grp.add(c) for c in remaining_cells]
            grp.set(ProductCondition(remaining_total))
            self.grid.group_merge(grp)
            
            self.group.detach()
            return True
    
    def symbol(self):
        return "%sx" % (self.value,)

class DivisionCondition(Condition):
    def validate(self):
        assert len(self.group) == 2, "DivisionCondition only works with 2-cell groups (%d here)!" % (len(self.group),)
        try:
            v0, v1 = [float(c.value) for c in self.group]
            div01, div10 = v0/v1, v1/v0
        except TypeError:
            return False
        return (self.value in (div01, div10))

    def process(self):
        # NOTE: only 2 cells! Otherwise division will be messed up!
        
        # Solutions are those numbers that, divided by each others, equal the desired value
        sols = set((v1, v2) for v1 in self.grid.nums for v2 in self.grid.nums \
                            if float(self.value) in (float(v1)/v2, float(v2)/v1))
        
        # all_values = set(all the values that are either in one cellor the other)
        #            = flatten(sols) (in a set, to remove duplicates)
        all_values = set(v for v1v2 in sols for v in v1v2)
        
        # Anything that is not in all values is in none of the cells!
        self.group.restrict(v for v in self.grid.nums if v not in all_values)
        
        # filter solutions to fit cell possible values
        sols = [s for s in sols if all((s[i] in self.group[i].possible) for i in range(len(s)))]
        
        log(0, 'SOLUTIONS', self.value, sols)
        
        self.group.info = sols
        
        # Values that are in every possibility of the group
        certain_values = [v for v in self.grid.nums if all(v in poss for poss in sols)]
        log(1, 'certain values:', certain_values)
        self.group.certain(certain_values)
        
        for i, c in enumerate(self.group):
            c.possible = set(s[i] for s in sols)
        
        self.desintegrate()
    
    def desintegrate(self):
        if all((c.value is not None) for c in self.group):
            self.group.detach()
            return True
        else:
            return False
    
    def symbol(self):
        return "%s/" % (self.value,)

class DifferenceCondition(Condition):
    def validate(self):
        assert len(self.group) == 2, "DifferenceCondition only works with 2-cell groups (%d here)!" % (len(self.group),)
        try:
            v0, v1 = [c.value for c in self.group]
            diff01, diff10 = v0-v1, v1-v0
        except TypeError:
            return False
        return (self.value in (diff01, diff10))

    def process(self):
        # NOTE: only 2 cells! Otherwise difference will be messed up!
        
        # Solutions are those numbers whose difference (in either way) equals the desired value
        sols = set((v1, v2) for v1 in self.grid.nums for v2 in self.grid.nums \
                            if abs(v1-v2) == self.value) # v1-v2 == self.value or v2-v1 == self.value
        
        # all_values = set(all the values that are either in one cellor the other)
        #            = flatten(sols) (in a set, to remove duplicates)
        all_values = set(v for v1v2 in sols for v in v1v2)
        
        # Anything that is not in all values is in none of the cells!
        self.group.restrict(v for v in self.grid.nums if v not in all_values)
        
        # filter solutions to fit cell possible values
        sols = [s for s in sols if all((s[i] in self.group[i].possible) for i in range(len(s)))]
        
        log(0, 'SOLUTIONS', self.value, sols)
        
        self.group.info = sols
        
        # Values that are in every possibility of the group
        certain_values = [v for v in self.grid.nums if all(v in poss for poss in sols)]
        log(1, 'certain values:', certain_values)
        self.group.certain(certain_values)
                
        for i, c in enumerate(self.group):
            c.possible = set(s[i] for s in sols)
        
        self.desintegrate()
    
    def desintegrate(self):
        if all((c.value is not None) for c in self.group):
            self.group.detach()
            return True
        else:
            return False
    
    def symbol(self):
        return "%s-" % (self.value,)

if __name__ == "__main__":
    DO_LOG = (raw_input("DO_LOG?(Y/N)").lower()[:1] == "y")
    
    from grids import all_grids
    
    print "Grids:"
    for name in all_grids:
        print "-", name

    possible_names = []
    while len(possible_names) != 1:
        name_start = raw_input("Which one?")
        if name_start in all_grids:
            possible_names = [name_start]
            break
        possible_names = [n for n in all_grids if n.startswith(name_start)]
    name = possible_names[0]
    
    size, info = all_grids[name]
    
    conds = {"=": EqualityCondition,
                "+": SumCondition, "-": DifferenceCondition,
                "*": ProductCondition, "/": DivisionCondition,
                "u": lambda v: UniqueCondition}
    
    g = Grid(size)
    
    for i in info:
        if size == "sudoku":
            blk = Group(g)
        else:
            blk = Block(g)
        v, op = int(i[0][:-1]), i[0][-1]
        
        try: Cond = conds[op]
        except KeyError:
            log("0", "#", "Unknown Condition!", op, "value", v)
            continue
        else: cond = Cond(v)
        blk.set(cond)
        
        [blk.add(g.at(*cpos)) for cpos in i[1:]]
    
    g.setup()
    
    g.display(False)
    
    print "Done!"
    
    def run():
        g.process()
        g.display()
    
    def opt_groups(enum=True):
        if enum:
            i = -1
            for i, grp in enumerate(g.groups):
                print i, "-", grp
            print "# Removed Groups:"
            for j, grp in enumerate(g.removed_groups):
                print i+j+1, "-", grp
        
        index = None
        while index is None:
            try:
                index = input("Which group?")
            except:
                return
        if index < len(g.groups):
            grp = g.groups[index]
        else:
            grp = g.removed_groups[index-len(g.groups)]
        
        print grp
        print "Type:", type(grp)
        print "Condition:", grp.condition
        print "Cells (", len(grp), ") :", grp.cells
        print "Certain:", grp.certain_values
        print "Included:", grp.included_groups
        print "Info:", grp.info
        
        again = (raw_input("Antoher?(Y/N)").upper()[:1] == "Y")
        return opt_groups(enum=False) if again else True
    
    def opt_cells(enum=True):
        if enum:
            for c in g:
                print c, '->', c.value
        xy = input("Which cell?")
        c = g.at(*xy)
        print c
        print "Position:", (c.x, c.y)
        print "Value:", c.value
        print "Possible:", c.possible
        print "Block:", c.block
        
        again = (raw_input("Antoher?(Y/N)").upper()[:1] == "Y")
        return opt_cells(enum=False) if again else True
    
    def opt_validate():
        if g.validate():
            print "Valid Grid!"
        else:
            print "Invalid Grid! :("
        return True
    
    its_ok = True
    while its_ok:
        do_run = (raw_input("Run again?(Y/N)").upper()[:1] == "Y")
        if do_run:
            run()
            continue
        
        print "Options:"
        options = { "q": ("Quit", lambda: False),
                    "g": ("List Groups", opt_groups),
                    "c": ("List cells", opt_cells),
                    "v": ("Validate grid", opt_validate)
                  }
        for opt, (label, callback) in options.iteritems():
            print opt, "-", label
        
        option = raw_input("What?").lower()[:1]
        if option not in options:
            print "Unknown Option!"
            its_ok = False
            continue
        
        if not options[option][1]():
            its_ok = False
            continue
    
    if g.validate():
        raise OverflowError, "Great! It worked"
    else:
        raise OverflowError, "WTF went wrong !?!"
