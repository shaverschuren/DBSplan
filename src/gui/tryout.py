from PyQt5 import QtWidgets, uic
import sys
import os


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi(os.path.join("gui", "ui_files", "TargetSelection.ui"), self)
        self.show()


app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.exec_()
