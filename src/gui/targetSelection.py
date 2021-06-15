"""Main Target Selection GUI
"""

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import nibabel as nib


class TargetSelection(pg.GraphicsLayoutWidget):

    def __init__(self):
        """Main window initialization"""
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
        """Screen initialization"""
        self.screen = QtGui.QDesktopWidget().screenGeometry()

        self.resize(1000, 800)
        self.setWindowState(QtCore.Qt.WindowMaximized)

    def initData(self):
        """Data initialization"""
        # Load nifti image for tryouts
        self.img = nib.load(
            "/mnt/d/DBSplan/tmpData/nifti/SEEGBCI-13/MRI_T1W.nii.gz"
        )
        self.data = np.array(self.img.get_fdata())
        self.shape = np.shape(self.data)

    def initSubplots(self):
        """Subplot initialization"""
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

        self.view_sag = "v1"
        self.view_fro = "v2"
        self.view_tra = "v3"

        # Define starting positions
        self.tra_pos = self.shape[2] // 2
        self.sag_pos = self.shape[0] // 2
        self.fro_pos = self.shape[1] // 2

        self.cursor_i = self.sag_pos
        self.cursor_j = self.fro_pos
        self.cursor_k = self.tra_pos

        self.current_hover = None

        # Setup viewboxes
        for v in [self.v1, self.v2, self.v3]:
            v.setAspectLocked(1.0)
            v.setMouseEnabled(x=False, y=False)
            v.setLimits(
                xMin=-1.5 * max(self.shape), xMax=max(self.shape) * 2.5,
                minXRange=20, maxXRange=max(self.shape) * 4.,
                yMin=-1.5 * max(self.shape), yMax=max(self.shape) * 2.5,
                minYRange=20, maxYRange=max(self.shape) * 4.
            )

        # Items for displaying image data
        self.img_tra = pg.ImageItem(self.data[:, :, self.tra_pos])
        self.img_fro = pg.ImageItem(self.data[:, self.fro_pos, :])
        self.img_sag = pg.ImageItem(self.data[self.sag_pos, :, :])

        self.v1.addItem(self.img_sag)
        self.v2.addItem(self.img_fro)
        self.v3.addItem(self.img_tra)

        # Add target point plots in all 3 images
        self.target_points = []
        self.target_points_sag = []
        self.target_points_fro = []
        self.target_points_tra = []

        self.tar_sag = pg.ScatterPlotItem(
            pos=self.target_points_sag,
            symbol="o", brush="b", pen="b", size=8
        )
        self.tar_fro = pg.ScatterPlotItem(
            pos=self.target_points_fro,
            symbol="o", brush="b", pen="b", size=8
        )
        self.tar_tra = pg.ScatterPlotItem(
            pos=self.target_points_tra,
            symbol="o", brush="b", pen="b", size=8
        )

        self.v1.addItem(self.tar_sag)
        self.v2.addItem(self.tar_fro)
        self.v3.addItem(self.tar_tra)

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

        self.img_tra.mouseDragEvent = self.imageMouseDragEvent_tra
        self.img_fro.mouseDragEvent = self.imageMouseDragEvent_fro
        self.img_sag.mouseDragEvent = self.imageMouseDragEvent_sag

        self.img_tra.keyPressEvent = self.imageKeyPressEvent_tra
        self.img_fro.keyPressEvent = self.imageKeyPressEvent_fro
        self.img_sag.keyPressEvent = self.imageKeyPressEvent_sag

        self.img_tra.wheelEvent = self.imageWheelEvent_tra
        self.img_fro.wheelEvent = self.imageWheelEvent_fro
        self.img_sag.wheelEvent = self.imageWheelEvent_sag

    def updateImages(self):
        """Updates images on event"""
        # Update images
        self.img_tra.setImage(self.data[:, :, self.tra_pos])
        self.img_fro.setImage(self.data[:, self.fro_pos, :])
        self.img_sag.setImage(self.data[self.sag_pos, :, :])

        # Update cursor plots
        self.cur_tra.setData(pos=[(self.cursor_i, self.cursor_j)])
        self.cur_fro.setData(pos=[(self.cursor_i, self.cursor_k)])
        self.cur_sag.setData(pos=[(self.cursor_j, self.cursor_k)])

        # Update target plots
        self.target_points_tra = []
        self.target_points_fro = []
        self.target_points_sag = []
        for target_point in self.target_points:
            if self.tra_pos == target_point[2]:
                self.target_points_tra.append(
                    (target_point[0], target_point[1])
                )
            if self.fro_pos == target_point[1]:
                self.target_points_fro.append(
                    (target_point[0], target_point[2])
                )
            if self.sag_pos == target_point[0]:
                self.target_points_sag.append(
                    (target_point[1], target_point[2])
                )
        self.tar_tra.setData(pos=self.target_points_tra)
        self.tar_fro.setData(pos=self.target_points_fro)
        self.tar_sag.setData(pos=self.target_points_sag)

    def updateText(self):
        """Updates text on event"""
        updated_string = (
            "Mouse: "
            f"[{self.hover_i:4d}, {self.hover_j:4d}, {self.hover_k:4d}]"
            "   |   "
            "Cursor: "
            f"[{self.cursor_i:4d}, {self.cursor_j:4d}, {self.cursor_k:4d}]"
        )

        self.text.setText(updated_string)

    def addTarget(self):
        """Adds current cursor position to target list"""
        target_point = (self.cursor_i, self.cursor_j, self.cursor_k)

        self.target_points.append(target_point)

    def zoomImage(self, delta, img_str):
        """Zooms in/out on a certain image"""
        scale_factor = 1.0 + delta * 0.1

        if img_str == "tra":
            x_scale = self.hover_i
            y_scale = self.hover_j
            view = self.view_tra
        elif img_str == "fro":
            x_scale = self.hover_i
            y_scale = self.hover_k
            view = self.view_fro
        elif img_str == "sag":
            x_scale = self.hover_j
            y_scale = self.hover_k
            view = self.view_sag

        if view == "v1":
            self.v1.scaleBy(
                s=[scale_factor, scale_factor],
                center=(x_scale, y_scale))
        elif view == "v2":
            self.v2.scaleBy(
                s=[scale_factor, scale_factor],
                center=(x_scale, y_scale))
        elif view == "v3":
            self.v3.scaleBy(
                s=[scale_factor, scale_factor],
                center=(x_scale, y_scale))

    def imageHoverEvent_tra(self, event):
        """Handles hover event on transverse plane"""
        view = "tra"
        self.current_hover = "tra"
        self.imageHoverEvent(event, view)

    def imageHoverEvent_fro(self, event):
        """Handles hover event on frontal plane"""
        view = "fro"
        self.current_hover = "fro"
        self.imageHoverEvent(event, view)

    def imageHoverEvent_sag(self, event):
        """Handles hover event on saggital plane"""
        view = "sag"
        self.current_hover = "sag"
        self.imageHoverEvent(event, view)

    def imageHoverEvent(self, event, view):
        """Show the voxel position under the mouse cursor."""

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
        """Handles click event on transverse plane"""
        view = "tra"
        self.imageMouseClickEvent(event, view)

    def imageMouseClickEvent_fro(self, event):
        """Handles click event on frontal plane"""
        view = "fro"
        self.imageMouseClickEvent(event, view)

    def imageMouseClickEvent_sag(self, event):
        """Handles click event on saggital plane"""
        view = "sag"
        self.imageMouseClickEvent(event, view)

    def imageMouseClickEvent(self, event, view):
        """ Update the current target/view point"""

        # Extract click position
        pos = event.pos()
        x, y = pos.y(), pos.x()

        if event.buttons() == QtCore.Qt.LeftButton:
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

    def imageMouseDragEvent_tra(self, event):
        """Handles drag event on transverse plane"""
        view = "tra"
        self.imageMouseDragEvent(event, view)

    def imageMouseDragEvent_fro(self, event):
        """Handles drag event on frontal plane"""
        view = "fro"
        self.imageMouseDragEvent(event, view)

    def imageMouseDragEvent_sag(self, event):
        """Handles drag event on saggital plane"""
        view = "sag"
        self.imageMouseDragEvent(event, view)

    def imageMouseDragEvent(self, event, view):
        """ Implementation of right drag panning"""

        # Manually accept event
        event.accept()

        # Check for right-click drag
        if event.button() == QtCore.Qt.RightButton:
            # Extract start position + update is this is a start
            if event.isStart():
                self.drag_startpos = event.buttonDownPos()
                self.drag_prevpos = event.pos()
            # Reset if this is the end
            elif event.isFinish():
                self.drag_startpos = None
                self.drag_prevpos = None
            # Translate image upon dragging
            else:
                prev_x = self.drag_prevpos.x()
                prev_y = self.drag_prevpos.y()

                current_x = event.pos().x()
                current_y = event.pos().y()

                # Check which viewbox to update
                if view == "tra":
                    view = self.view_tra
                elif view == "fro":
                    view = self.view_fro
                elif view == "sag":
                    view = self.view_sag

                # Update appropriate viewbox
                if view == "v1":
                    self.v1.translateBy(
                        x=-(current_x - prev_x), y=-(current_y - prev_y)
                    )
                elif view == "v2":
                    self.v2.translateBy(
                        x=-(current_x - prev_x), y=-(current_y - prev_y)
                    )
                elif view == "v3":
                    self.v3.translateBy(
                        x=-(current_x - prev_x), y=-(current_y - prev_y)
                    )

                # Update "previous" position
                self.drag_prevpos = event.pos()

    def keyPressEvent(self, event):
        """Handles general keypress events"""
        self.scene().keyPressEvent(event)

        if self.current_hover == "tra":
            self.imageKeyPressEvent_tra(event)
        if self.current_hover == "fro":
            self.imageKeyPressEvent_fro(event)
        if self.current_hover == "sag":
            self.imageKeyPressEvent_sag(event)

    def imageKeyPressEvent_tra(self, event):
        """Handles keypress event on transverse plane"""
        view = "tra"
        self.imageKeyPressEvent(event, view)

    def imageKeyPressEvent_fro(self, event):
        """Handles keypress event on frontal plane"""
        view = "fro"
        self.imageKeyPressEvent(event, view)

    def imageKeyPressEvent_sag(self, event):
        """Handles keypress event on saggital plane"""
        view = "sag"
        self.imageKeyPressEvent(event, view)

    def imageKeyPressEvent(self, event, view):
        """ Handles key presses
        - Up/down -> scrolling
        - Return -> Add target point
        """

        # Checks for up/down key presses (scroll)
        if event.key() in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down):
            # Define direction
            if event.key() == QtCore.Qt.Key_Up:
                scroll = 1
            elif event.key() == QtCore.Qt.Key_Down:
                scroll = -1

            # Adjust cursor + view position
            if view == "tra":
                if self.cursor_k > 0 and self.cursor_k < self.shape[2] - 1:
                    self.tra_pos += scroll
                    self.cursor_k += scroll
            elif view == "fro":
                if self.cursor_j > 0 and self.cursor_j < self.shape[1] - 1:
                    self.fro_pos += scroll
                    self.cursor_j += scroll
            elif view == "sag":
                if self.cursor_i > 0 and self.cursor_i < self.shape[0] - 1:
                    self.sag_pos += scroll
                    self.cursor_i += scroll

            # Update images
            self.updateImages()

        # Checks for a Return/Enter key (add Target)
        elif event.key() == QtCore.Qt.Key_Return:
            # Add target
            self.addTarget()
            # Update plots
            self.updateImages()

    def imageWheelEvent_tra(self, event):
        """Handles mousewheel event on transverse plane"""
        view = "tra"
        self.imageWheelEvent(event, view)

    def imageWheelEvent_fro(self, event):
        """Handles mousewheel event on frontal plane"""
        view = "fro"
        self.imageWheelEvent(event, view)

    def imageWheelEvent_sag(self, event):
        """Handles mousewheel event on saggital plane"""
        view = "sag"
        self.imageWheelEvent(event, view)

    def imageWheelEvent(self, event, view):
        """ Zoom using mouse wheel"""

        # Check for mouse wheel movement direction
        if event.delta() > 0:
            # Wheel away from user -> zoom in
            delta = 1
        else:
            # Wheel towards user -> zoom out
            delta = -1

        # Zoom appropriate image
        self.zoomImage(delta, view)


if __name__ == '__main__':

    target_selection = TargetSelection()
    target_selection.show()

    pg.QtGui.QApplication.exec_()
