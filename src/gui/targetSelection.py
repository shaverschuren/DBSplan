"""Main Target Selection GUI
"""

import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import numpy as np
import nibabel as nib
from util.nifti import load_nifti


class TargetSelection(QtWidgets.QWidget):

    def __init__(self, paths):
        """Main window initialization"""
        super().__init__()

        # Load paths and settings
        self.paths = paths

        # Setup main window
        self.initScreen()
        # Setup data
        self.initData()
        # Setup subplots widget
        self.initSubplots()
        # Setup top bar
        self.initTop()
        # Setup side bar
        self.initSide()

        # Setup main layout
        self.initWindow()

    def initScreen(self):
        """Screen initialization"""
        self.setWindowTitle('Target Selection')

        self.screen = QtGui.QDesktopWidget().screenGeometry()
        self.resize(1000, 800)
        self.setWindowState(QtCore.Qt.WindowMaximized)

    def initWindow(self):
        """Main window initialization"""

        # Layout of main window
        layout = QtGui.QGridLayout()

        layout.addWidget(self.topBar, 0, 0, 1, 1)
        layout.addWidget(self.sideBar, 0, 5, 2, 1)
        layout.addWidget(self.subplots, 1, 0, 1, 5)

        self.setLayout(layout)

    def initData(self):
        """Data initialization"""
        # Load basic images (T1W, T1W-GADO, CT)
        scan1_arr, scan1_aff, _ = load_nifti(self.paths["T1w"])
        scan1_name = "T1w"
        scan2_arr, scan2_aff, _ = load_nifti(self.paths["T1w_gado"])
        scan2_name = "T1w_gado"
        scan3_arr, scan3_aff, _ = load_nifti(self.paths["CT"])
        scan3_name = "CT"

        # Load scans in dict
        self.scans = {
            scan1_name: scan1_arr,
            scan2_name: scan2_arr,
            scan3_name: scan3_arr,
        }

        # Set starting data and shape
        self.data = scan1_arr
        self.aff = scan1_aff
        self.shape = np.shape(self.data)

    def initSubplots(self):
        """Subplot initialization"""

        # Create PyQtGraph graphics widget
        self.subplots = pg.GraphicsLayoutWidget()
        self.subplots.ci.setBorder((50, 50, 100))

        # Setup top
        self.subplots.sub_text = self.subplots.addLayout(
            col=1, row=1, colspan=2, rowspan=1)

        # Setup image plots
        self.subplots.sub1 = self.subplots.addLayout(
            col=1, row=2, colspan=2, rowspan=1)
        self.subplots.sub2 = self.subplots.addLayout(
            col=1, row=3, colspan=1, rowspan=1)
        self.subplots.sub3 = self.subplots.addLayout(
            col=2, row=3, colspan=1, rowspan=1)

        # Constrain top
        self.subplots.sub_text.setMaximumHeight(30)

        # Add viewboxes
        self.subplots.v1 = self.subplots.sub1.addViewBox()
        self.subplots.v2 = self.subplots.sub2.addViewBox()
        self.subplots.v3 = self.subplots.sub3.addViewBox()

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

        self.hover_i = self.sag_pos
        self.hover_j = self.fro_pos
        self.hover_k = self.tra_pos

        self.current_hover = None

        # Setup viewboxes
        for v in [self.subplots.v1, self.subplots.v2, self.subplots.v3]:
            v.setMouseEnabled(x=False, y=False)
            v.setLimits(
                xMin=-1.0 * max(self.shape), xMax=max(self.shape) * 2.0,
                minXRange=20, maxXRange=max(self.shape) * 4.,
                yMin=-1.0 * max(self.shape), yMax=max(self.shape) * 2.0,
                minYRange=20, maxYRange=max(self.shape) * 4.
            )

        # Setup aspect ratios (for anisotropic resolutions)
        self.updateAspectRatios()

        # Items for displaying image data
        self.subplots.img_tra = pg.ImageItem(self.data[:, :, self.tra_pos])
        self.subplots.img_fro = pg.ImageItem(self.data[:, self.fro_pos, :])
        self.subplots.img_sag = pg.ImageItem(self.data[self.sag_pos, :, :])

        self.subplots.v1.addItem(self.subplots.img_sag)
        self.subplots.v2.addItem(self.subplots.img_fro)
        self.subplots.v3.addItem(self.subplots.img_tra)

        # Add target point plots in all 3 images
        self.target_points = []
        self.target_points_sag = []
        self.target_points_fro = []
        self.target_points_tra = []

        self.subplots.tar_sag = pg.ScatterPlotItem(
            pos=self.target_points_sag,
            symbol="o", brush="b", pen="b", size=8
        )
        self.subplots.tar_fro = pg.ScatterPlotItem(
            pos=self.target_points_fro,
            symbol="o", brush="b", pen="b", size=8
        )
        self.subplots.tar_tra = pg.ScatterPlotItem(
            pos=self.target_points_tra,
            symbol="o", brush="b", pen="b", size=8
        )

        self.subplots.v1.addItem(self.subplots.tar_sag)
        self.subplots.v2.addItem(self.subplots.tar_fro)
        self.subplots.v3.addItem(self.subplots.tar_tra)

        # Add cursor in all 3 images
        self.subplots.cur_sag = pg.ScatterPlotItem(
            pos=[(self.cursor_j, self.cursor_k)],
            symbol="+", brush="r", pen="r", size=6
        )
        self.subplots.cur_fro = pg.ScatterPlotItem(
            pos=[(self.cursor_i, self.cursor_k)],
            symbol="+", brush="r", pen="r", size=6
        )
        self.subplots.cur_tra = pg.ScatterPlotItem(
            pos=[(self.cursor_i, self.cursor_j)],
            symbol="+", brush="r", pen="r", size=6
        )

        self.subplots.v1.addItem(self.subplots.cur_sag)
        self.subplots.v2.addItem(self.subplots.cur_fro)
        self.subplots.v3.addItem(self.subplots.cur_tra)

        # Display text bar
        infoStr = (
            "Mouse: "
            f"[{0:4d}, {0:4d}, {0:4d}]"
            "    |    "
            "Cursor: "
            f"[{0:4d}, {0:4d}, {0:4d}]"
        )

        self.text = pg.LabelItem(
            infoStr, color=(255, 255, 255), size="10pt"
        )

        self.subplots.sub_text.addItem(self.text)

        # Disable right click menus
        self.subplots.v1.setMenuEnabled(False)
        self.subplots.v2.setMenuEnabled(False)
        self.subplots.v3.setMenuEnabled(False)

        # Fix scaling
        self.subplots.v1.autoRange()
        self.subplots.v2.autoRange()
        self.subplots.v3.autoRange()

        # Setup events
        self.subplots.img_tra.hoverEvent = self.imageHoverEvent_tra
        self.subplots.img_fro.hoverEvent = self.imageHoverEvent_fro
        self.subplots.img_sag.hoverEvent = self.imageHoverEvent_sag

        self.subplots.img_tra.mouseClickEvent = self.imageMouseClickEvent_tra
        self.subplots.img_fro.mouseClickEvent = self.imageMouseClickEvent_fro
        self.subplots.img_sag.mouseClickEvent = self.imageMouseClickEvent_sag

        self.subplots.img_tra.mouseDragEvent = self.imageMouseDragEvent_tra
        self.subplots.img_fro.mouseDragEvent = self.imageMouseDragEvent_fro
        self.subplots.img_sag.mouseDragEvent = self.imageMouseDragEvent_sag

        # self.subplots.img_tra.keyPressEvent = self.imageKeyPressEvent_tra
        # self.subplots.img_fro.keyPressEvent = self.imageKeyPressEvent_fro
        # self.subplots.img_sag.keyPressEvent = self.imageKeyPressEvent_sag

        self.subplots.keyPressEvent = self.keyPressEvent

        self.subplots.img_tra.wheelEvent = self.imageWheelEvent_tra
        self.subplots.img_fro.wheelEvent = self.imageWheelEvent_fro
        self.subplots.img_sag.wheelEvent = self.imageWheelEvent_sag

    def initTop(self):
        """Initialize top bar"""

        self.topBar = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout()

        # Setup buttons
        self.button_tra = QtGui.QPushButton('tra')
        self.button_tra.clicked.connect(self.changeView_tra)
        self.button_fro = QtGui.QPushButton('fro')
        self.button_fro.clicked.connect(self.changeView_fro)
        self.button_sag = QtGui.QPushButton('sag')
        self.button_sag.clicked.connect(self.changeView_sag)

        # Display buttons
        layout.addWidget(self.button_tra)
        layout.addWidget(self.button_fro)
        layout.addWidget(self.button_sag)

        self.topBar.setLayout(layout)

        self.topBar.setMaximumHeight(40)
        self.topBar.setMaximumWidth(100)

    def initSide(self):
        """Initializes the sidebar"""

        # Initialize widget
        self.sideBar = QtWidgets.QWidget()

        # Setup layout
        layout = QtWidgets.QVBoxLayout()
        self.sideBar.setLayout(layout)
        self.sideBar.setMaximumWidth(200)

        # Add labels
        self.targetLabel = QtWidgets.QLabel("Target points")
        self.scanLabel = QtWidgets.QLabel("Scans")

        # Add target point list
        self.targetList = QtWidgets.QListWidget()
        self.targetList.clicked.connect(self.selectTarget)

        # Add scans list
        self.scanList = QtWidgets.QListWidget()
        self.scanList.clicked.connect(self.selectScan)

        row = 0
        for scan_name in self.scans.keys():
            self.scanList.insertItem(row, scan_name)
            row += 1

        # Add lists and labels to layout
        layout.addWidget(self.targetLabel)
        layout.addWidget(self.targetList)
        layout.addWidget(self.scanLabel)
        layout.addWidget(self.scanList)

    def updateImages(self):
        """Updates images on event"""
        # Update images
        self.subplots.img_tra.setImage(self.data[:, :, self.tra_pos])
        self.subplots.img_fro.setImage(self.data[:, self.fro_pos, :])
        self.subplots.img_sag.setImage(self.data[self.sag_pos, :, :])

        # Update cursor plots
        self.subplots.cur_tra.setData(pos=[(self.cursor_i, self.cursor_j)])
        self.subplots.cur_fro.setData(pos=[(self.cursor_i, self.cursor_k)])
        self.subplots.cur_sag.setData(pos=[(self.cursor_j, self.cursor_k)])

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
        self.subplots.tar_tra.setData(pos=self.target_points_tra)
        self.subplots.tar_fro.setData(pos=self.target_points_fro)
        self.subplots.tar_sag.setData(pos=self.target_points_sag)

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

    def updateAspectRatios(self):
        """Updates the aspect ratios of the view boxes"""

        # Extract voxel sizes in i,j,k dimensions
        dim_i = np.diag(self.aff)[0]
        dim_j = np.diag(self.aff)[1]
        dim_k = np.diag(self.aff)[2]

        # Calculate aspect ratios
        self.aspect_ratio_tra = dim_i / dim_j
        self.aspect_ratio_fro = dim_i / dim_k
        self.aspect_ratio_sag = dim_j / dim_k

        # Set aspect ratios to appropriate viewboxes
        for aspect_ratio, plane in [
            (self.aspect_ratio_tra, "tra"),
            (self.aspect_ratio_fro, "fro"),
            (self.aspect_ratio_sag, "sag"),
        ]:
            if self.view_v1 == plane:
                self.subplots.v1.setAspectLocked(
                    lock=True, ratio=abs(aspect_ratio))
                if aspect_ratio < 0:
                    self.subplots.v1.invertX()
            elif self.view_v2 == plane:
                self.subplots.v2.setAspectLocked(
                    lock=True, ratio=abs(aspect_ratio))
                if aspect_ratio < 0:
                    self.subplots.v2.invertX()
            elif self.view_v3 == plane:
                self.subplots.v3.setAspectLocked(
                    lock=True, ratio=abs(aspect_ratio))
                if aspect_ratio < 0:
                    self.subplots.v3.invertX()

    def addTarget(self):
        """Adds current cursor position to target list"""

        # Define current target point
        target_point = (self.cursor_i, self.cursor_j, self.cursor_k)

        # Append target point list
        self.target_points.append(target_point)

        # Update target list widget
        self.targetList.clear()
        for point_i in range(len(self.target_points)):
            self.targetList.insertItem(
                point_i, str(self.target_points[point_i])
            )

        # Update images
        self.updateImages()
        self.updateText()

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
            self.subplots.v1.scaleBy(
                s=[scale_factor, scale_factor],
                center=(x_scale, y_scale))
        elif view == "v2":
            self.subplots.v2.scaleBy(
                s=[scale_factor, scale_factor],
                center=(x_scale, y_scale))
        elif view == "v3":
            self.subplots.v3.scaleBy(
                s=[scale_factor, scale_factor],
                center=(x_scale, y_scale))

    def changeView_tra(self):
        """Handles clicking on the 'tra' button"""
        view = "tra"
        self.changeView(view)

    def changeView_fro(self):
        """Handles clicking on the 'fro' button"""
        view = "fro"
        self.changeView(view)

    def changeView_sag(self):
        """Handles clicking on the 'sag' button"""
        view = "sag"
        self.changeView(view)

    def changeView(self, view):
        """Handles changing views via button presses"""

        # Obtain current views
        current_v1 = self.view_v1

        # Define new views
        if view == "tra":
            new_v1 = "tra"
            new_v2 = "sag"
            new_v3 = "fro"
            new_tra = "v1"
            new_fro = "v3"
            new_sag = "v2"
        elif view == "fro":
            new_v1 = "fro"
            new_v2 = "sag"
            new_v3 = "tra"
            new_tra = "v3"
            new_fro = "v1"
            new_sag = "v2"
        elif view == "sag":
            new_v1 = "sag"
            new_v2 = "fro"
            new_v3 = "tra"
            new_tra = "v3"
            new_fro = "v2"
            new_sag = "v1"

        # Make the switch if necessary
        if current_v1 is not new_v1:

            # Remove old images
            self.subplots.v1.clear()
            self.subplots.v2.clear()
            self.subplots.v3.clear()

            # Loop over viewboxes and replace images
            for v, new in [
                (self.subplots.v1, new_v1),
                (self.subplots.v2, new_v2),
                (self.subplots.v3, new_v3)
            ]:

                # Add new image
                if new == "tra":
                    v.addItem(self.subplots.img_tra)
                    v.addItem(self.subplots.tar_tra)
                    v.addItem(self.subplots.cur_tra)
                elif new == "fro":
                    v.addItem(self.subplots.img_fro)
                    v.addItem(self.subplots.tar_fro)
                    v.addItem(self.subplots.cur_fro)
                elif new == "sag":
                    v.addItem(self.subplots.img_sag)
                    v.addItem(self.subplots.tar_sag)
                    v.addItem(self.subplots.cur_sag)

                # Adjust range
                v.autoRange()

            # Update params
            self.view_v1 = new_v1
            self.view_v2 = new_v2
            self.view_v3 = new_v3

            self.view_tra = new_tra
            self.view_fro = new_fro
            self.view_sag = new_sag

            # Update images
            self.updateAspectRatios()
            self.updateImages()
            self.updateText()

    def selectTarget(self):
        """Updates currently selected target"""

        # Obtain (cleaned up) target string
        target_str = self.targetList.currentItem().text()
        target_str = target_str.replace("(", "").replace(")", "")

        # Split string and store as tuple[int]
        target_split = target_str.split(", ")
        self.selectedTarget = tuple([int(target) for target in target_split])

        # Set view to target
        self.sag_pos = self.selectedTarget[0]
        self.fro_pos = self.selectedTarget[1]
        self.tra_pos = self.selectedTarget[2]

        self.cursor_i = self.selectedTarget[0]
        self.cursor_j = self.selectedTarget[1]
        self.cursor_k = self.selectedTarget[2]

        self.updateImages()
        self.updateText()

    def selectScan(self):
        """Updates the scan currently in view"""

        # Obtain scan name
        scan_name = self.scanList.currentItem().text()

        # Update view data field
        self.data = self.scans[scan_name]
        self.shape = np.shape(self.data)

        # Update image/text
        self.updateImages()
        self.updateText()

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
            self.updateText()

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
                    self.subplots.v1.translateBy(
                        x=-(current_x - prev_x), y=-(current_y - prev_y)
                    )
                elif view == "v2":
                    self.subplots.v2.translateBy(
                        x=-(current_x - prev_x), y=-(current_y - prev_y)
                    )
                elif view == "v3":
                    self.subplots.v3.translateBy(
                        x=-(current_x - prev_x), y=-(current_y - prev_y)
                    )

                # Update "previous" position
                self.drag_prevpos = event.pos()

        self.updateText()

    def keyPressEvent(self, event):
        """Handles general keypress events"""
        # self.scene().keyPressEvent(event)

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
            # Update text
            self.updateText()

        # Checks for a Return/Enter key (add Target)
        elif event.key() == QtCore.Qt.Key_Return:
            # Add target
            self.addTarget()
            # Update plots
            self.updateImages()

        elif event.key() == QtCore.Qt.Key_Delete:

            # Delete selected target (if applicable)
            if "selectedTarget" in dir(self):
                if self.selectedTarget in self.target_points:
                    self.target_points.remove(self.selectedTarget)

                # Update target list widget
                self.targetList.clear()
                for point_i in range(len(self.target_points)):
                    self.targetList.insertItem(
                        point_i, str(self.target_points[point_i])
                    )

                # Update images
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

        # Update text
        self.updateText()


def main(subject_paths):
    """Main function for target point selection GUI"""

    app = QtGui.QApplication(sys.argv)

    target_selection = TargetSelection(subject_paths)
    target_selection.show()

    QtGui.QApplication.exec_()

    if len(target_selection.target_points) > 0:
        return target_selection.target_points
    else:
        raise UserWarning("No target points were selected!"
                          " Exiting...")


if __name__ == '__main__':
    main({})
