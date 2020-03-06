from __future__ import annotations
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QPushButton, QVBoxLayout, QLabel, QGridLayout

from widgets.cameraView import CircleCenterOverlay
import typing
if typing.TYPE_CHECKING:
    from camera_gui import Window


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