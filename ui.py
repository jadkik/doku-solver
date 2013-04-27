from PyQt4 import QtGui, QtCore
import sys
from main import *
from grids import all_grids
from random import choice

class MainWindow(QtGui.QWidget):
    
    def __init__(self, grid_name):
        super(MainWindow, self).__init__()
        
        self.load(grid_name)
        self.layout = QtGui.QGridLayout()
        self.text = {}
        
        for (x, y), cell in self.grid.cells.iteritems():
            text = QtGui.QLineEdit()
            text.textEdited.connect(lambda it, ix=x, iy=y: self.onTextChanged(it, ix, iy))
            if cell.value is not None:
                text.setText(str(cell.value))
            else:
                text.setText("")
            text.setPlaceholderText(cell.block.condition.symbol())
            text.setInputMask("D")
            text.setFixedSize(QtCore.QSize(40, 40))
            
            pal = text.palette();
            pal.setColor(text.backgroundRole(), self.color(cell));
            text.setPalette(pal);
            
            self.layout.addWidget(text, y, x)
            self.text[x,y] = text
        
        self.solve = QtGui.QPushButton("Solve")
        self.solve.clicked.connect(self.onSolvePressed)
        
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addLayout(self.layout)
        mainLayout.addWidget(self.solve)
        
        self.setLayout(mainLayout)
        
        # Set tab order to be able to switch from cell to cell
        # Should be called only after setting the main layout
        def iterpos(size):
            for y in range(size):
                for x in range(size):
                    yield (x, y)
        
        it = iterpos(self.grid.size)
        last_pos = it.next()
        self.text[last_pos].setFocus()
        for (x, y) in it:
            self.text[x, y].setTabOrder(self.text[last_pos], self.text[x, y])
            last_pos = (x, y)
    
    __colors = {}
    __all_colors = frozenset([QtCore.Qt.blue, QtCore.Qt.red, QtCore.Qt.white, QtCore.Qt.magenta,
                    QtCore.Qt.green, QtCore.Qt.yellow, QtCore.Qt.cyan, QtCore.Qt.darkGreen,
                    QtCore.Qt.lightGray, QtCore.Qt.darkMagenta, QtCore.Qt.gray, QtCore.Qt.darkGray,
                    QtCore.Qt.darkCyan, QtCore.Qt.darkYellow])
    __rem_colors = set()
    def color(self, cell):
        try:
            return self.__colors[id(cell.block)]
        except KeyError:
            if len(self.__rem_colors) == 0:
                self.__rem_colors = set(self.__all_colors)
            col = self.__rem_colors.pop()
            self.__colors[id(cell.block)] = col
            return col
        
    
    def load(self, name):
        
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
        self.grid = g
    
    def updateGrid(self):
        for (x, y), cell in self.grid.cells.iteritems():
            if cell.value is not None:
                self.text[x,y].setText(str(cell.value))
    
    def check(self):
        if self.grid.validate():
            QtGui.QMessageBox.information(self, "You won!", "You won the game.")
            self.close()
    
    def onTextChanged(self, text, x, y):
        try:
            self.grid.cells[x, y].value = int(text)
        except (ValueError, TypeError):
            pass
        else:
            self.grid.display()
            print '*'*10
            print
        
        self.check()
    
    def onSolvePressed(self):
        self.grid.process()
        self.updateGrid()
        self.check()

if __name__ == "__main__":
    
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
    
    app = QtGui.QApplication(sys.argv)
    MainWindow(name).show()
    app.exec_()
        