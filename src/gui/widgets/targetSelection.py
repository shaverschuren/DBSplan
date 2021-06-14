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
        self.resize(1000, 1000)
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
        self.nextRow()
        self.sub1 = self.addLayout(colspan=2)
        self.nextRow()
        self.sub2 = self.addLayout()
        self.sub3 = self.addLayout()

        # Constrain text row height
        self.sub0.setMaximumHeight(30)

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
            # v.setMouseEnabled(x=False, y=False)
            v.setLimits(
                xMin=-0.5 * max(self.shape), xMax=max(self.shape) * 1.5,
                minXRange=10, maxXRange=max(self.shape) * 2.5,
                yMin=-0.5 * max(self.shape), yMax=max(self.shape) * 1.5,
                minYRange=10, maxYRange=max(self.shape) * 2.5
            )

        # Item for displaying image data
        img_tra = pg.ImageItem(self.data[:, :, 128])
        img_fro = pg.ImageItem(self.data[:, 128, :])
        img_sag = pg.ImageItem(self.data[128, :, :])

        self.v1.addItem(img_sag)
        self.v2.addItem(img_fro)
        self.v3.addItem(img_tra)

        # Display text bar
        self.infoStr = "Voxel: (000, 000, 000)"
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
        self.v1.hoverEvent = self.imageHoverEvent_v1
        self.v2.hoverEvent = self.imageHoverEvent_v2
        self.v3.hoverEvent = self.imageHoverEvent_v3

    def imageHoverEvent_v1(self, event):
        view = self.view_v1
        self.imageHoverEvent(event, view)

    def imageHoverEvent_v2(self, event):
        view = self.view_v2
        self.imageHoverEvent(event, view)

    def imageHoverEvent_v3(self, event):
        view = self.view_v3
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


# # Load nifti image for tryouts
# img = nib.load("/mnt/d/DBSplan/tmpData/nifti/SEEGBCI-13/MRI_T1W.nii.gz")
# data = np.array(img.get_fdata())
# shape = np.shape(data)

# # Interpret image data as row-major instead of col-major
# # pg.setConfigOptions(imageAxisOrder='row-major')

# pg.mkQApp()
# win = pg.GraphicsLayoutWidget(show=True)
# win.setWindowTitle('Target Selection')
# win.resize(1000, 600)
# win.setWindowState(QtCore.Qt.WindowMaximized)
# win.ci.setBorder((50, 50, 100))

# # A plot area (ViewBox + axes) for displaying the images
# sub1 = win.addLayout(colspan=2)
# win.nextRow()
# sub2 = win.addLayout()
# sub3 = win.addLayout()

# # Add viewboxes
# v1 = sub1.addViewBox()
# v2 = sub2.addViewBox()
# v3 = sub3.addViewBox()

# # Setup viewboxes
# for v in [v1, v2, v3]:
#     v.setAspectLocked(1.0)
#     v.setMouseEnabled(x=False, y=False)
#     v.setLimits(
#         xMin=-0.5 * max(shape), xMax=max(shape) * 1.5,
#         minXRange=10, maxXRange=max(shape) * 2.5,
#         yMin=-0.5 * max(shape), yMax=max(shape) * 1.5,
#         minYRange=10, maxYRange=max(shape) * 2.5
#     )

# # Item for displaying image data
# img_tra = pg.ImageItem(data[128, :, :])
# img_sag = pg.ImageItem(data[:, 128, :])
# img_fro = pg.ImageItem(data[:, :, 128])

# v1.addItem(img_tra)
# v2.addItem(img_sag)
# v3.addItem(img_fro)

# # Custom ROI for selecting an image region
# roi = pg.ROI([-8, 14], [6, 5])
# roi.addScaleHandle([0.5, 1], [0.5, 0.5])
# roi.addScaleHandle([0, 0.5], [0.5, 0.5])
# p1.addItem(roi)
# roi.setZValue(10)  # make sure ROI is drawn above image

# # Contrast/color control
# hist = pg.HistogramLUTItem()
# hist.setImageItem(img)
# win.addItem(hist)

# Draggable line for setting isocurve level
# isoLine = pg.InfiniteLine(angle=0, movable=True, pen='g')
# # hist.vb.addItem(isoLine)
# # hist.vb.setMouseEnabled(y=False) # makes user interaction a little easier
# isoLine.setValue(0.8)
# isoLine.setZValue(1000) # bring iso line above contrast controls

# Another plot area for displaying ROI data
# win.nextRow()
# p2 = win.addPlot(colspan=2)
# p2.setMaximumHeight(250)


# # Generate image data
# data = np.random.normal(size=(200, 100))
# data[20:80, 20:80] += 2.
# data = pg.gaussianFilter(data, (3, 3))
# data += np.random.normal(size=(200, 100)) * 0.1
# img.setImage(data)
# hist.setLevels(data.min(), data.max())

# build isocurves from smoothed data
# iso.setData(pg.gaussianFilter(data, (2, 2)))

# set position and scale of image
# tr = QtGui.QTransform()
# img_tra.setTransform(tr.scale(0.2, 0.2).translate(-50, 0))

# zoom to fit imageo
# v1.autoRange()
# v2.autoRange()
# v3.autoRange()

# Callbacks for handling user interaction
# def updatePlot():
#     global img, roi, data, p2
#     # selected = roi.getArrayRegion(data, img)
#     # p2.plot(selected.mean(axis=0), clear=True)

# roi.sigRegionChanged.connect(updatePlot)
# updatePlot()


# def updateIsocurve():
#     global isoLine, iso
#     iso.setLevel(isoLine.value())

# isoLine.sigDragged.connect(updateIsocurve)


# def imageHoverEvent(event):
#     """Show the position, pixel, and value under the mouse cursor.
#     """
#     if event.isExit():
#         p1.setTitle("")
#         return
#     pos = event.pos()
#     i, j = pos.y(), pos.x()

#     i = int(np.clip(i, 0, np.shape(img_tra)[0] - 1))
#     j = int(np.clip(j, 0, np.shape(img_tra)[1] - 1))
#     val = img_tra[i, j]
#     # ppos = img_tra.mapToParent(pos)
#     # x, y = ppos.x(), ppos.y()
#     p1.setTitle("pixel: (%d, %d)  value: %g" % (i, j, val))


# # Monkey-patch the image to use our custom hover function.
# # This is generally discouraged (you should subclass ImageItem instead),
# # but it works for a very simple use like this.
# img_tra.hoverEvent = imageHoverEvent


if __name__ == '__main__':

    target_selection = TargetSelection()
    target_selection.show()

    pg.QtGui.QApplication.exec_()
