"""
Demonstrates common image analysis tools.
Many of the features demonstrated here are already provided by the ImageView
widget, but here we present a lower-level approach that provides finer control
over the user interface.
"""

import warnings
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import nibabel as nib


class TargetSelection(pg.GraphicsLayoutWidget):

    def __init__(self):
        super().__init__()

        # Setup main window
        pg.mkQApp()
        self.setWindowTitle('Target Selection')
        self.ci.setBorder((50, 50, 100))

        # Setup window size
        self.initScreen()

        # Setup data
        self.initData()

        # Setup subplots
        self.initSubplots()

    def initScreen(self):
        self.screen = QtGui.QDesktopWidget().screenGeometry()

        self.resize(1000, 800)
        self.setWindowState(QtCore.Qt.WindowMaximized)

    def initData(self):
        # Load nifti image for tryouts
        self.img = nib.load(
            "/mnt/d/DBSplan/tmpData/nifti/SEEGBCI-13/MRI_T1W.nii.gz"
        )
        self.data = np.array(self.img.get_fdata())
        self.shape = np.shape(self.data)

    def initSubplots(self):
        # Setup subplots
        self.sub0 = self.addLayout(colspan=2)
        self.sub4 = self.addLayout(rowspan=3)
        self.nextRow()
        self.sub1 = self.addLayout(colspan=2)
        self.nextRow()
        self.sub2 = self.addLayout()
        self.sub3 = self.addLayout()

        # Constrain text row height
        self.sub0.setMaximumHeight(30)
        self.sub4.setMaximumWidth(200)

        # Add viewboxes
        self.v0 = self.sub0.addViewBox()
        self.v1 = self.sub1.addViewBox()
        self.v2 = self.sub2.addViewBox()
        self.v3 = self.sub3.addViewBox()

        # Add labels for image viewboxes
        self.view_v1 = "sag"
        self.view_v2 = "fro"
        self.view_v3 = "tra"

        self.tra_pos = self.shape[2] // 2
        self.sag_pos = self.shape[0] // 2
        self.fro_pos = self.shape[1] // 2

        self.cursor_i = self.sag_pos
        self.cursor_j = self.fro_pos
        self.cursor_k = self.tra_pos

        # Setup viewboxes
        for v in [self.v1, self.v2, self.v3]:
            v.setAspectLocked(1.0)
            v.setMouseEnabled(x=False, y=False)
            v.setLimits(
                xMin=-1.5 * max(self.shape), xMax=max(self.shape) * 2.5,
                minXRange=10, maxXRange=max(self.shape) * 4.,
                yMin=-1.5 * max(self.shape), yMax=max(self.shape) * 2.5,
                minYRange=10, maxYRange=max(self.shape) * 4.
            )

        # Items for displaying image data
        self.img_tra = pg.ImageItem(self.data[:, :, self.tra_pos])
        self.img_fro = pg.ImageItem(self.data[:, self.fro_pos, :])
        self.img_sag = pg.ImageItem(self.data[self.sag_pos, :, :])

        self.v1.addItem(self.img_sag)
        self.v2.addItem(self.img_fro)
        self.v3.addItem(self.img_tra)

        # Add cursor in all 3 images
        self.cur_sag = pg.ScatterPlotItem(
            pos=[(self.cursor_j, self.cursor_k)],
            symbol="+", brush="r", pen="r", size=6
        )
        self.cur_fro = pg.ScatterPlotItem(
            pos=[(self.cursor_i, self.cursor_k)],
            symbol="+", brush="r", pen="r", size=6
        )
        self.cur_tra = pg.ScatterPlotItem(
            pos=[(self.cursor_i, self.cursor_j)],
            symbol="+", brush="r", pen="r", size=6
        )

        self.v1.addItem(self.cur_sag)
        self.v2.addItem(self.cur_fro)
        self.v3.addItem(self.cur_tra)

        # Disable right click menus
        self.v1.setMenuEnabled(False)
        self.v2.setMenuEnabled(False)
        self.v3.setMenuEnabled(False)

        # Display text bar
        infoStr = (
            "Mouse: "
            f"[{0:4d}, {0:4d}, {0:4d}]"
            "   |   "
            "Cursor: "
            f"[{0:4d}, {0:4d}, {0:4d}]"
        )

        font = QtGui.QFont()
        font.setPixelSize(10)
        self.text = pg.TextItem(
            infoStr, (255, 255, 255), anchor=(0.5, 0.5)
        )
        self.text.setFont(font)
        self.v0.addItem(self.text)

        self.v0.setMouseEnabled(x=False, y=False)

        # Fix scaling
        self.v1.autoRange()
        self.v2.autoRange()
        self.v3.autoRange()

        # Setup events
        self.img_tra.hoverEvent = self.imageHoverEvent_tra
        self.img_fro.hoverEvent = self.imageHoverEvent_fro
        self.img_sag.hoverEvent = self.imageHoverEvent_sag

        self.img_tra.mouseClickEvent = self.imageMouseClickEvent_tra
        self.img_fro.mouseClickEvent = self.imageMouseClickEvent_fro
        self.img_sag.mouseClickEvent = self.imageMouseClickEvent_sag

    def updateImages(self):
        self.img_tra.setImage(self.data[:, :, self.tra_pos])
        self.img_fro.setImage(self.data[:, self.fro_pos, :])
        self.img_sag.setImage(self.data[self.sag_pos, :, :])

        self.cur_tra.setData(pos=[(self.cursor_i, self.cursor_j)])
        self.cur_fro.setData(pos=[(self.cursor_i, self.cursor_k)])
        self.cur_sag.setData(pos=[(self.cursor_j, self.cursor_k)])

    def updateText(self):
        updated_string = (
            "Mouse: "
            f"[{self.hover_i:4d}, {self.hover_j:4d}, {self.hover_k:4d}]"
            "   |   "
            "Cursor: "
            f"[{self.cursor_i:4d}, {self.cursor_j:4d}, {self.cursor_k:4d}]"
        )

        self.text.setText(updated_string)

    def imageHoverEvent_tra(self, event):
        view = "tra"
        self.imageHoverEvent(event, view)

    def imageHoverEvent_fro(self, event):
        view = "fro"
        self.imageHoverEvent(event, view)

    def imageHoverEvent_sag(self, event):
        view = "sag"
        self.imageHoverEvent(event, view)

    def imageHoverEvent(self, event, view):
        """Show the voxel position under the mouse cursor.
        """

        if event.isExit():
            self.hover_i = 0
            self.hover_j = 0
            self.hover_k = 0

            self.updateText()
            return

        pos = event.pos()
        x, y = pos.y(), pos.x()

        if view == "tra":
            self.hover_i = int(np.clip(y, 0, self.shape[0] - 1))
            self.hover_j = int(np.clip(x, 0, self.shape[1] - 1))
            self.hover_k = int(self.tra_pos)
        elif view == "fro":
            self.hover_i = int(np.clip(y, 0, self.shape[0] - 1))
            self.hover_j = int(self.fro_pos)
            self.hover_k = int(np.clip(x, 0, self.shape[2] - 1))
        elif view == "sag":
            self.hover_i = int(self.sag_pos)
            self.hover_j = int(np.clip(y, 0, self.shape[1] - 1))
            self.hover_k = int(np.clip(x, 0, self.shape[2] - 1))

        if QtCore.Qt.LeftButton == event.buttons():
            self.sag_pos = self.hover_i
            self.fro_pos = self.hover_j
            self.tra_pos = self.hover_k

            self.cursor_i = self.hover_i
            self.cursor_j = self.hover_j
            self.cursor_k = self.hover_k

            self.updateImages()

        self.updateText()

    def imageMouseClickEvent_tra(self, event):
        view = "tra"
        self.imageMouseClickEvent(event, view)

    def imageMouseClickEvent_fro(self, event):
        view = "fro"
        self.imageMouseClickEvent(event, view)

    def imageMouseClickEvent_sag(self, event):
        view = "sag"
        self.imageMouseClickEvent(event, view)

    def imageMouseClickEvent(self, event, view):
        """ Update the current target/view point
        """

        # Extract click position
        pos = event.pos()
        x, y = pos.y(), pos.x()

        if QtCore.Qt.LeftButton == event.buttons():
            # Update view
            if view == "tra":
                self.sag_pos = int(np.clip(y, 0, self.shape[0] - 1))
                self.fro_pos = int(np.clip(x, 0, self.shape[1] - 1))
            elif view == "fro":
                self.sag_pos = int(np.clip(y, 0, self.shape[0] - 1))
                self.tra_pos = int(np.clip(x, 0, self.shape[2] - 1))
            elif view == "sag":
                self.fro_pos = int(np.clip(y, 0, self.shape[1] - 1))
                self.tra_pos = int(np.clip(x, 0, self.shape[2] - 1))

            self.cursor_i = self.sag_pos
            self.cursor_j = self.fro_pos
            self.cursor_k = self.tra_pos

            self.updateImages()


if __name__ == '__main__':

    target_selection = TargetSelection()
    target_selection.show()

    pg.QtGui.QApplication.exec_()
