import sys
if "" not in sys.path: sys.path.append("")
if "src" not in sys.path: sys.path.append("src")

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # setting title
        self.setWindowTitle("Python ")

        # setting geometry
        self.setGeometry(100, 100, 1200, 800)

        # calling method
        self.UiComponents()

        # showing all the widgets
        self.showMaximized()

    # method for widgets
    def UiComponents(self):

        # creating label
        label = QLabel("Label", self)

        # setting geometry to label
        label.setGeometry(100, 100, 120, 40)

        # adding border to label
        label.setStyleSheet("border : 2px solid black")

        # opening window in maximized size
        self.showMaximized()


def ScanSelection(paths, settings):

    raise UserWarning("The scan selection GUI is not implemented yet!")


if __name__ == "__main__":
    ScanSelection(..., ...)
