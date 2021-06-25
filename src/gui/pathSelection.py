"""Main Path Selection GUI
"""

import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import numpy as np
from util.nifti import load_nifti


class PathSelection(QtWidgets.QWidget):

    def __init__(self, paths, all_trajectories):
        """Main window initialization"""
        super().__init__()

        # Load paths and trajectories
        self.paths = paths
        self.all_trajectories = all_trajectories

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

        # Load distance map
        self.distance_map, dist_aff, _ = \
            load_nifti(self.paths["distance_map_combined"])

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

        self.vox_dims = np.diag(self.aff)[:-1]

        # Setup initial trajectory
        self.n_targets = np.shape(self.all_trajectories)[0]

        self.target_i = 0
        self.trajectory_i = 0

        self.updateTrajectory()

    def initSubplots(self):
        """Subplot initialization"""

        # Create PyQtGraph graphics widget
        self.subplots = pg.GraphicsLayoutWidget()
        self.subplots.ci.setBorder((50, 50, 100))

        # Setup top
        self.subplots.sub_text = self.subplots.addLayout(
            col=0, row=0, colspan=2, rowspan=1)

        # Setup image plots
        self.subplots.sub1 = self.subplots.addLayout(
            col=0, row=1, colspan=1, rowspan=1)
        self.subplots.sub2 = self.subplots.addLayout(
            col=1, row=1, colspan=1, rowspan=1)
        self.subplots.sub3 = self.subplots.addLayout(
            col=0, row=2, colspan=2, rowspan=1)

        # Constrain top + graph
        self.subplots.sub_text.setMaximumHeight(30)
        self.subplots.sub3.setMaximumHeight(100)

        # Add viewboxes
        self.subplots.v_probe = self.subplots.sub1.addViewBox()
        self.subplots.v_3d = self.subplots.sub2.addViewBox()

        self.subplots.v_graph = pg.PlotItem()
        self.subplots.sub3.addItem(self.subplots.v_graph)

        # Init probe-eye view
        self.updateProbeView()

        # Add probe-eye slice
        self.subplots.img_probe = pg.ImageItem(self.current_slice)
        self.subplots.v_probe.addItem(
            self.subplots.img_probe
        )

        # Add probe marker
        self.subplots.probe_marker = pg.ScatterPlotItem(
            pos=[(max(self.shape) // 2, max(self.shape) // 2)],
            symbol="o", brush="b", pen="b", size=6
        )
        self.subplots.v_probe.addItem(self.subplots.probe_marker)
        # Add probe margin
        self.subplots.probe_margin = pg.ScatterPlotItem(
            pos=[(max(self.shape) // 2, max(self.shape) // 2)],
            symbol="o", brush=(0, 100, 100, 100), pen="b", size=24
        )
        self.subplots.v_probe.addItem(self.subplots.probe_margin)

        # TODO: For testing ...
        self.subplots.v_3d.addItem(
            pg.ImageItem(self.current_slice)
        )

        # Setup viewbox limits + disable default mouse commands
        for v in [self.subplots.v_probe, self.subplots.v_3d]:
            v.setMouseEnabled(x=False, y=False)
            v.setLimits(
                xMin=-1.0 * max(self.shape), xMax=max(self.shape) * 2.0,
                minXRange=20, maxXRange=max(self.shape) * 4.,
                yMin=-1.0 * max(self.shape), yMax=max(self.shape) * 2.0,
                minYRange=20, maxYRange=max(self.shape) * 4.
            )
            v.setAspectLocked(self.aspect_y / self.aspect_x)

        self.subplots.v_graph.autoRange()
        self.subplots.v_3d.autoRange()

        # Setup distance plot
        self.subplots.v_graph.plot(
            x=self.trajectory_dist2entryList, y=self.trajectory_distances)
        self.subplots.v_graph.setMouseEnabled(x=False, y=False)

        # # Disable right click menus
        self.subplots.v_probe.setMenuEnabled(False)
        self.subplots.v_3d.setMenuEnabled(False)
        self.subplots.v_graph.setMenuEnabled(False)

        # # Fix scaling
        self.subplots.v_probe.autoRange()
        self.subplots.v_graph.autoRange()

        # # Setup events
        # self.subplots.img_tra.hoverEvent = self.imageHoverEvent_tra
        # self.subplots.img_fro.hoverEvent = self.imageHoverEvent_fro
        # self.subplots.img_sag.hoverEvent = self.imageHoverEvent_sag

        # self.subplots.img_tra.mouseClickEvent = self.imageMouseClickEvent_tra
        # self.subplots.img_fro.mouseClickEvent = self.imageMouseClickEvent_fro
        # self.subplots.img_sag.mouseClickEvent = self.imageMouseClickEvent_sag

        # self.subplots.img_tra.mouseDragEvent = self.imageMouseDragEvent_tra
        # self.subplots.img_fro.mouseDragEvent = self.imageMouseDragEvent_fro
        # self.subplots.img_sag.mouseDragEvent = self.imageMouseDragEvent_sag

        # # self.subplots.img_tra.keyPressEvent = self.imageKeyPressEvent_tra
        # # self.subplots.img_fro.keyPressEvent = self.imageKeyPressEvent_fro
        # # self.subplots.img_sag.keyPressEvent = self.imageKeyPressEvent_sag

        self.subplots.keyPressEvent = self.keyPressEvent

        self.subplots.img_probe.wheelEvent = self.imageWheelEvent_probe
        # self.subplots.img_fro.wheelEvent = self.imageWheelEvent_fro
        # self.subplots.img_sag.wheelEvent = self.imageWheelEvent_sag

    def initTop(self):
        """Initialize top bar"""

        self.topBar = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout()

        # Setup buttons
        self.button_tra = QtGui.QPushButton('tra')
        # self.button_tra.clicked.connect(self.changeView_tra)
        self.button_fro = QtGui.QPushButton('fro')
        # self.button_fro.clicked.connect(self.changeView_fro)
        self.button_sag = QtGui.QPushButton('sag')
        # self.button_sag.clicked.connect(self.changeView_sag)

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

        # Update slice
        self.updateProbeView()
        # Update image
        self.subplots.img_probe.setImage(self.current_slice)

    def updateProbeView(self):
        """Updates the probe eye view and performs data slicing"""

        # Update current position
        self.current_pos = self.trajectory_checkpoints[self.checkpoint_i]
        # Update current slice
        self.current_slice = self.trajectory_slices[self.checkpoint_i]

    def define_checkpoints(self):
        """Define checkpoints along current trajectory"""

        start = np.array(self.current_entry)
        stop = np.array(self.current_target)

        trajectory_vector = stop - start

        self.trajectory_checkpoints = np.zeros((100, 3))
        self.trajectory_dist2entryList = np.zeros(100)
        self.trajectory_distances = np.zeros(100)

        for i in range(100):
            # Define checkpoint coordinates
            checkpoint = start + trajectory_vector * (i / 99)
            # Define distance to entry (mm)
            dist2entry = np.sqrt(np.sum(
                [(self.vox_dims[j] * trajectory_vector[j] * (i / 99)) ** 2
                    for j in range(3)]
            ))
            # Define distance to critical structure
            checkpoint_idx = np.round(checkpoint)
            distance = self.distance_map[
                int(checkpoint_idx[0]),
                int(checkpoint_idx[1]),
                int(checkpoint_idx[2])
            ]
            # Store found results
            self.trajectory_checkpoints[i] = checkpoint
            self.trajectory_dist2entryList[i] = dist2entry
            self.trajectory_distances[i] = distance

    def updateTrajectory(self):
        """Handles selection of new trajectory"""

        # Select new current trajectory
        self.current_trajectory = \
            self.all_trajectories[self.target_i][self.trajectory_i]

        # Store direction, entry, target
        self.current_direction = tuple(self.current_trajectory[0])
        self.current_entry = tuple(self.current_trajectory[1])
        self.current_target = tuple(self.current_trajectory[2])

        # Define checkpoints
        self.define_checkpoints()

        # Define proper vectors. These vectors should both be
        # perpendicular to the trajectory direction vector and
        # to each other.
        n = np.array(object=self.current_direction)
        n = n / (n[0] ** 2 + n[1] ** 2 + n[2] ** 2)

        vector1 = (
            np.array([1, 1, -(n[0] + n[1]) / n[2]]) /
            (1 ** 2 + 1 ** 2 + (-(n[0] + n[1]) / n[2]) ** 2)
        )
        vector2 = np.cross(n, vector1)

        # Define shape
        self.slice_shape = (max(self.shape), max(self.shape))

        # Determine proper aspect ratios
        self.aspect_y = np.sqrt(sum(
            [(vector1[i] * self.vox_dims[i]) ** 2 for i in range(3)]
        ))
        self.aspect_x = np.sqrt(sum(
            [(vector2[i] * self.vox_dims[i]) ** 2 for i in range(3)]
        ))

        # Setup vectors in appropriate format
        self.vectors = tuple((tuple(vector1), tuple(vector2)))

        # Loop over checkpoints and slice data
        self.trajectory_slices = np.zeros((
            len(self.trajectory_checkpoints),
            self.slice_shape[0],
            self.slice_shape[1]
        ))

        for checkpoint_i in range(len(self.trajectory_checkpoints)):
            slice_origin = tuple(
                np.array(self.trajectory_checkpoints[checkpoint_i]) -
                (max(self.shape) // 2) * (vector1 + vector2)
            )

            self.trajectory_slices[checkpoint_i] = pg.functions.affineSlice(
                self.data, self.slice_shape, slice_origin, self.vectors,
                axes=(0, 1, 2), order=0
            )

        # Setup current position to target checkpoint
        self.checkpoint_i = len(self.trajectory_checkpoints) - 1
        self.current_pos = \
            tuple(self.trajectory_checkpoints[self.checkpoint_i])

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

        if img_str == "probe":
            x_scale = self.slice_shape[0] // 2
            y_scale = self.slice_shape[1] // 2
            self.subplots.v_probe.scaleBy(
                s=[scale_factor, scale_factor],
                center=(x_scale, y_scale))
        elif img_str == "3d":
            pass

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
        # self.updateText()

    def selectScan(self):
        """Updates the scan currently in view"""

        # Obtain scan name
        scan_name = self.scanList.currentItem().text()

        # Update view data field
        self.data = self.scans[scan_name]
        self.shape = np.shape(self.data)

        # Update slicing
        self.updateTrajectory()
        # Update image/text
        self.updateImages()
        # self.updateText()

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

        self.imageKeyPressEvent(event)

    def imageKeyPressEvent(self, event):
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

            # Setup new checkpoint (if not on edge)
            if ((
                scroll > 0 and
                self.checkpoint_i >= len(self.trajectory_checkpoints) - 1
            ) or (
                scroll < 0 and self.checkpoint_i == 0
            )):
                pass
            else:
                self.checkpoint_i += scroll

            # Update probe view
            # self.updateProbeView()
            self.updateImages()

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

    def imageWheelEvent_probe(self, event):
        """Handles mousewheel event on probe view"""
        view = "probe"
        self.imageWheelEvent(event, view)

    def imageWheelEvent_3d(self, event):
        """Handles mousewheel event on 3d view"""
        view = "3d"
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
        # self.updateText()


def main(subject_paths, suggested_trajectories):
    """Main function for path selection GUI"""

    app = QtGui.QApplication(sys.argv)

    path_selection = PathSelection(
        subject_paths, suggested_trajectories)
    path_selection.show()

    QtGui.QApplication.exec_()

    return path_selection.all_trajectories

    # if len(path_selection.target_points) > 0:
    #     return path_selection.target_points
    # else:
    #     raise UserWarning("No target points were selected!"
    #                       " Exiting...")


if __name__ == '__main__':
    main({})
