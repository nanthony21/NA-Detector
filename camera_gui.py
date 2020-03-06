# -*- coding: utf-8 -*-
# Copyright 2015-2017 Nate Bogdanowicz
"""
A very simple GUI that uses a CameraView to view live video from a camera.
"""
from __future__ import annotations
import sys

from PyQt5  import QtCore
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QPen, QPixmap, QPainter
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton,
                             QVBoxLayout, QHBoxLayout, QSizePolicy, QCheckBox, QDialog, QGridLayout, QFormLayout, QSpinBox, QDoubleSpinBox, QLabel)
from instrumental import instrument, list_instruments

import os

from cameraView import CircleOverlayCameraView, Overlay, CircleOverlay, CircleCenterOverlay
from hardware import TestCamera
from widgets import AspectRatioWidget

os.environ['PATH'] += os.path.abspath('lib') #This makes is so that the Camera driver DLL can be found.


class App(QApplication):
    def __init__(self, argv, camera):
        super().__init__(argv)
        self.camera = camera
        self.camview = CircleOverlayCameraView(camera)
        self.window = Window(self.camview)
        self.window.show()

        
class Window(QMainWindow):
    def __init__(self, camview: CircleOverlayCameraView):
        super().__init__()
        self.setWindowTitle("NA Detector")
        self.advancedDlg = AdvancedDialog(self, camview)
        self.cameraView = camview

        self.button = QPushButton("Start Video")
        self.btn_grab = QPushButton("Grab Frame")
        self.advancedButton = QPushButton("Advanced...")
        
        self.arWidget = AspectRatioWidget(camview.arr.shape[1] / camview.arr.shape[0], self)
        self.arWidget.setLayout(QVBoxLayout())
        self.arWidget.layout().addWidget(camview)

        def start_stop():
            if not self.cameraView.isRunning:
                camview.start_video()
                self.button.setText("Stop Video")
                self.btn_grab.setEnabled(False)
            else:
                camview.stop_video()
                self.button.setText("Start Video")
                self.btn_grab.setEnabled(True)
        self.button.clicked.connect(start_stop)
        
        def grab():
            camview.grab_image()
        self.btn_grab.clicked.connect(grab)

        def showAdvanced():
            self.advancedDlg.show()

            # Move dialog to the side
            rect = self.advancedDlg.geometry()
            newPoint = self.mapToGlobal(QPoint(-rect.width(), 0))
            rect.moveTo(newPoint)
            self.advancedDlg.setGeometry(rect)

        self.advancedButton.released.connect(showAdvanced)

        main_area = QWidget(self)
        main_area.setLayout(QGridLayout())
        button_area = QWidget()
        button_area.setLayout(QHBoxLayout())
        fittingWidget = FittingWidget(self)


        # Fill Layouts
        l = main_area.layout()
        l.addWidget(self.arWidget, 0, 0)
        l.addWidget(button_area, 1, 0)
        l.addWidget(fittingWidget, 0, 1, 2, 1)
        l.setRowStretch(0, 1)

        l = button_area.layout()
        l.addStretch()  # Makes the buttons move over rather than spread out.
        l.addWidget(self.button)
        l.addWidget(self.btn_grab)
        l.addWidget(self.advancedButton)

        # Attach some child widgets directly
        self.setCentralWidget(main_area)


class FittingWidget(QWidget):
    def __init__(self, parent: Window = None):
        super().__init__(parent)

        self._naPerPix = 0
        self._objCenter = (0, 0)
        self._measCenter = (0, 0)

        self.objectiveD = QDoubleSpinBox(self)
        self.objectiveNA = QDoubleSpinBox(self)
        self.objectiveX = QDoubleSpinBox(self)
        self.objectiveY = QDoubleSpinBox(self)
        self.measureObjectiveButton = QPushButton("Measure Objective Aperture", self)
        self.targetD = QDoubleSpinBox(self)
        self.targetNA = QDoubleSpinBox(self)
        self.drawTargetButton = QPushButton("Draw Target Aperture", self)
        self.measureTargetButton = QPushButton("Measure Aperture", self)

        self.objectiveOverlay = CircleCenterOverlay(QtCore.Qt.NoBrush, QtCore.Qt.blue, 0, 0, 0)
        self.measuredOverlay = CircleCenterOverlay(QtCore.Qt.NoBrush, QtCore.Qt.green, 0, 0, 0)
        self.targetOverlay = CircleCenterOverlay(QtCore.Qt.NoBrush, QtCore.Qt.cyan, 0, 0, 0)
        parent.cameraView.addOverlay(self.objectiveOverlay)
        parent.cameraView.addOverlay(self.measuredOverlay)
        parent.cameraView.addOverlay(self.targetOverlay)

        #configure limits
        for i in [self.objectiveD, self.targetD, self.objectiveX, self.objectiveY]:
            i.setMinimum(0)
            i.setMaximum(100000000)
            i.setSingleStep(1)

        for i in [self.objectiveNA, self.targetNA]:
            i.setMaximum(100000000)
            i.setMinimum(0)
            i.setSingleStep(0.1)

        def measTarg():
            x, y, r = parent.cameraView.fitCoords
            self._measCenter = (x, y)
            self.targetD.setValue(r*2)
        self.measureTargetButton.released.connect(measTarg)

        def targChanged():
            self.targetNA.setValue(self._naPerPix * self.targetD.value())
            self.measuredOverlay.active = True
            self.measuredOverlay.x = self._measCenter[0]
            self.measuredOverlay.y = self._measCenter[1]
            self.measuredOverlay.r = self.targetD.value() / 2
            if not parent.cameraView.isRunning:
                parent.cameraView.refresh()
        self.targetD.valueChanged.connect(targChanged)


        def objChanged():
            d = self.objectiveD.value()
            if d != 0:
                self._naPerPix = self.objectiveNA.value() / d
            self._objCenter = (self.objectiveX.value(), self.objectiveY.value())
            self.objectiveOverlay.active = True
            self.objectiveOverlay.x = self._objCenter[0]
            self.objectiveOverlay.y = self._objCenter[1]
            self.objectiveOverlay.r = d/2
            targChanged()
        self.objectiveNA.valueChanged.connect(objChanged)
        self.objectiveD.valueChanged.connect(objChanged)
        self.objectiveX.valueChanged.connect(objChanged)
        self.objectiveY.valueChanged.connect(objChanged)

        def measObj():
            x, y, r = parent.cameraView.fitCoords
            self.objectiveX.setValue(x)
            self.objectiveY.setValue(y)
            self.objectiveD.setValue(r*2)
        self.measureObjectiveButton.released.connect(measObj)

        def drawTarg():
            if self._naPerPix != 0:
                self.targetOverlay.active = True
                self.targetOverlay.x = self._objCenter[0]
                self.targetOverlay.y = self._objCenter[1]
                self.targetOverlay.r = self.targetNA.value() / self._naPerPix / 2
            else:
                self.targetOverlay.active = False
            if not parent.cameraView.isRunning:
                parent.cameraView.refresh()
        self.drawTargetButton.released.connect(drawTarg)

        l = QVBoxLayout()
        l.setAlignment(QtCore.Qt.AlignTop)
        lab = QLabel("Objective:")
        f = lab.font()
        f.setBold(True)
        lab.setFont(f)
        l.addWidget(lab)
        gl = QGridLayout()
        gl.addWidget(QLabel("Diameter (px):"), 0, 0)
        gl.addWidget(self.objectiveD, 0, 1)
        gl.addWidget(self.measureObjectiveButton, 0, 2)
        gl.addWidget(QLabel("Center (x,y):"), 1, 0)
        gl.addWidget(self.objectiveX, 1, 1)
        gl.addWidget(self.objectiveY, 1, 2)
        gl.addWidget(QLabel("NA:"), 2, 0)
        gl.addWidget(self.objectiveNA, 2, 1)
        l.addLayout(gl)
        lab = QLabel("Target:")
        f = lab.font()
        f.setBold(True)
        lab.setFont(f)
        l.addWidget(lab)
        gl = QGridLayout()
        gl.addWidget(QLabel("Diameter (px):"), 0, 0)
        gl.addWidget(self.targetD, 0, 1)
        gl.addWidget(self.measureTargetButton, 0, 2)
        gl.addWidget(QLabel("NA"), 1, 0)
        gl.addWidget(self.targetNA, 1, 1)
        gl.addWidget(self.drawTargetButton, 1, 2)
        l.addLayout(gl)
        l.addStretch() #Causes the bottom of the layout to push the rest upwards
        self.setLayout(l)


class AdvancedDialog(QDialog):
    def __init__(self, parent: QWidget, camview: CircleOverlayCameraView):
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings")
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint) #Get rid of the close button. this is handled by the selector widget active status

        self.viewBinary = QCheckBox("View Binary Image:", self)
        self.viewBinary.setLayoutDirection(QtCore.Qt.RightToLeft)  # Put label on left side of box
        def setBinary():
            camview.displayBinary = self.viewBinary.isChecked()
        self.viewBinary.stateChanged.connect(setBinary)
        self.viewBinary.setChecked(camview.displayBinary)

        self.viewPreOpt = QCheckBox("View initial guess:", self)
        self.viewPreOpt.setLayoutDirection(QtCore.Qt.RightToLeft)  # Put label on left side of box
        def viewPreOpt():
            camview.preOptFitOverlay.active = self.viewPreOpt.isChecked()
        self.viewPreOpt.stateChanged.connect(viewPreOpt)
        self.viewPreOpt.setChecked(camview.preOptFitOverlay.active)

        layout = QVBoxLayout()
        layout.addWidget(self.viewBinary)
        layout.addWidget(self.viewPreOpt)
        self.setLayout(layout)


if __name__ == '__main__':
    test = True

    cam = None
    if test:
        cam = TestCamera((512,1024), 10)
    else:
        inst = list_instruments()
        print(f"Found {len(inst)} cameras:")
        print(inst)
        if len(inst) > 0:
            cam = instrument(list_instruments()[0])  # Replace with your camera's alias

    if cam is not None:
        with cam:
            app = App(sys.argv, cam)
            app.exec_()
        
