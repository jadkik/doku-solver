from PyQt4 import QtGui, QtCore
import sys
from main import EqualityCondition, SumCondition, ProductCondition, UniqueCondition, \
        DifferenceCondition, DivisionCondition, Grid, Block, Group
from grids import all_grids

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
            text.setInputMask("D")
            
            if self.grid.sudoku:
                try:
                    cond = (g.condition for g in cell.groups if isinstance(g.condition, EqualityCondition)).next()
                    text.setPlaceholderText(cond.symbol())
                    text.setText(str(cond.value))
                except StopIteration:
                    text.setPlaceholderText("")
            else:
                text.setPlaceholderText(cell.block.condition.symbol())
            
            text.setFixedSize(QtCore.QSize(40, 40))
            
            pal = text.palette();
            pal.setColor(text.backgroundRole(), self.color(cell));
            text.setPalette(pal);
            
            self.layout.addWidget(text, y, x)
            self.text[x,y] = text
        
        self.label = QtGui.QLabel(grid_name)
        
        buttonBox = QtGui.QDialogButtonBox()
        self.solve = buttonBox.addButton("Solve", QtGui.QDialogButtonBox.ActionRole)
        self.select = buttonBox.addButton("Select", QtGui.QDialogButtonBox.ActionRole)
        self.exit = buttonBox.addButton("Exit", QtGui.QDialogButtonBox.ActionRole)
        
        self.solve.clicked.connect(self.onSolvePressed)
        self.select.clicked.connect(self.onSelectPressed)
        self.exit.clicked.connect(self.onExitPressed)
        
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.label)
        mainLayout.addLayout(self.layout)
        mainLayout.addWidget(buttonBox)
        
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
            
            try:
                Cond = conds[op]
            except KeyError:
                log("0", "#", "Unknown Condition!", op, "value", v)
                continue
            else:
                cond = Cond(v)
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
    
    def onSelectPressed(self):
        dlg = SelectDialog()
        dlg.exec_()
        if dlg.result():
            self.close()
    
    def onExitPressed(self):
        self.close()

class SelectDialog(QtGui.QDialog):
    name = None
    
    def __init__(self):
        super(SelectDialog, self).__init__()
        
        self.filter = QtGui.QLineEdit()
        self.filter.textEdited.connect(self.onFilter)
        
        self.list = QtGui.QListWidget()
        self.list.itemActivated.connect(self.onSelect)
        
        buttonBox = QtGui.QDialogButtonBox()
        ok = buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        cancel = buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        
        ok.clicked.connect(self.onOkPressed)
        cancel.clicked.connect(self.onCancelPressed)
        
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.filter)
        layout.addWidget(self.list)
        layout.addWidget(buttonBox)
        
        self.filter.setFocus()
        
        self.setLayout(layout)
        
        self.populate()
    
    def populate(self, text=None):
        self.list.clear()
        if text:
            self.items = [name for name in all_grids if text in name]
        else:
            self.items = all_grids.keys()
        self.list.addItems(self.items)
        self.list.setSelectionMode(QtGui.QListWidget.SingleSelection)
        self.list.setCurrentRow(0)
    
    def select(self):
        try:
            self.name = str(self.list.selectedItems()[0].text())
        except IndexError:
            self.name = None
        else:
            MainWindow(self.name).show()
            self.accept()
    
    def onOkPressed(self):
        self.select()
    
    def onCancelPressed(self):
        self.name = None
        self.reject()
    
    def onFilter(self):
        self.populate(str(self.filter.text()))
    
    def onSelect(self):
        self.select()

if __name__ == "__main__":
    
    app = QtGui.QApplication(sys.argv)
    dlg = SelectDialog()
    dlg.show()
    app.exec_()
        