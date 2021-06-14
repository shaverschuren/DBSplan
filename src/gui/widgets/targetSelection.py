"""
Demonstrates common image analysis tools.
Many of the features demonstrated here are already provided by the ImageView
widget, but here we present a lower-level approach that provides finer control
over the user interface.
"""

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
        self.resize(1000, 800)
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.ci.setBorder((50, 50, 100))

        # Setup data
        self.initData()

        # Setup subplots
        self.initSubplots()

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

        self.tra_pos = 128
        self.sag_pos = 128
        self.fro_pos = 128

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

        # Display text bar
        self.infoStr = "Voxel: [???, ???, ???]"
        self.text = pg.TextItem(
            self.infoStr, (255, 255, 255), anchor=(0.5, 0.5)
        )
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
        """Show the position, pixel, and value under the mouse cursor.
        """
        if event.isExit():
            self.text.setText(f"Voxel: [???, ???, ???]")
            return
        pos = event.pos()
        x, y = pos.y(), pos.x()

        if view == "tra":
            i = int(np.clip(x, 0, self.shape[0] - 1))
            j = int(np.clip(y, 0, self.shape[1] - 1))
            k = int(self.tra_pos)
        elif view == "fro":
            i = int(np.clip(x, 0, self.shape[0] - 1))
            j = int(self.fro_pos)
            k = int(np.clip(y, 0, self.shape[2] - 1))
        elif view == "sag":
            i = int(self.sag_pos)
            j = int(np.clip(x, 0, self.shape[1] - 1))
            k = int(np.clip(y, 0, self.shape[2] - 1))

        self.text.setText(f"Voxel: [{i:3d}, {j:3d}, {k:3d}]")


if __name__ == '__main__':

    target_selection = TargetSelection()
    target_selection.show()

    pg.QtGui.QApplication.exec_()
