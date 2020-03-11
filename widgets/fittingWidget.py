from __future__ import annotations
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QPushButton, QVBoxLayout, QLabel, QGridLayout, QFrame, QCheckBox

from widgets.cameraView import CircleCenterOverlay
import typing
if typing.TYPE_CHECKING:
    from mainWindow import Window


class FittingWidget(QFrame):

    def setupObjectivePanel(self) -> QGridLayout:
        self.objectiveD = QDoubleSpinBox(self)
        self.objectiveNA = QDoubleSpinBox(self)
        self.objectiveX = QDoubleSpinBox(self)
        self.objectiveY = QDoubleSpinBox(self)
        self.measureObjectiveButton = QPushButton("Measure Reference Aperture", self)
        displayCheckbox = QCheckBox("Display Overlay:", self)
        # configure limits
        for i in [self.objectiveD, self.objectiveX, self.objectiveY]:
            i.setMinimum(0)
            i.setMaximum(100000000)
            i.setSingleStep(1)

        i = self.objectiveNA
        i.setMaximum(100000000)
        i.setMinimum(0)
        i.setSingleStep(0.1)

        def updateOverlay():
            self.objectiveOverlay.active = True
            self.objectiveOverlay.x = self._objCenter[0]
            self.objectiveOverlay.y = self._objCenter[1]
            self.objectiveOverlay.r = d / 2
            if not self.parentWindow.cameraView.isRunning:
                self.parentWindow.cameraView.refresh()

        def objChanged():
            d = self.objectiveD.value()
            if d != 0:
                self._naPerPix = self.objectiveNA.value() / d
            self._objCenter = (self.objectiveX.value(), self.objectiveY.value())
            updateOverlay()

            self.targetNA.valueChanged.emit(0) #Trigger the targChanged() function. Not sure what the number should be or if it matters.
        self.objectiveNA.valueChanged.connect(objChanged)
        self.objectiveD.valueChanged.connect(objChanged)
        self.objectiveX.valueChanged.connect(objChanged)
        self.objectiveY.valueChanged.connect(objChanged)

        def measObj():
            x, y, r = self.parentWindow.cameraView.fitCoords
            self.objectiveX.setValue(x)
            self.objectiveY.setValue(y)
            self.objectiveD.setValue(r*2)
        self.measureObjectiveButton.released.connect(measObj)

        def displayCB():
            if displayCheckbox.checkState():
                self.objectiveOverlay.active = True
            else:
                self.objectiveOverlay.active = False
            updateOverlay()
        displayCheckbox.stateChanged.connect(displayCB)
        displayCheckbox.setChecked(True)

        gl = QGridLayout()
        gl.addWidget(QLabel("Diameter (px):"), 0, 0)
        gl.addWidget(self.objectiveD, 0, 1, 1, 2)
        gl.addWidget(QLabel("Center (x,y):"), 1, 0)
        gl.addWidget(self.objectiveX, 1, 1)
        gl.addWidget(self.objectiveY, 1, 2)
        gl.addWidget(QLabel("NA:"), 2, 0)
        gl.addWidget(self.objectiveNA, 2, 1, 1, 2)
        gl.addWidget(displayCheckbox, 3, 0, 1, 3)
        gl.addWidget(self.measureObjectiveButton, 4, 0, 1, 3)
        return gl

    def setupMeasurePanel(self) -> QGridLayout:
        self.measD = QDoubleSpinBox(self)
        self.measNA = QDoubleSpinBox(self)
        self.measX = QDoubleSpinBox(self)
        self.measY = QDoubleSpinBox(self)
        self.measureApertureButton = QPushButton("Measure Aperture", self)
        displayCheckbox = QCheckBox("Display Overlay:", self)

        # configure limits
        for i in [self.measX, self.measY, self.measD]:
            i.setMinimum(0)
            i.setMaximum(100000000)
            i.setSingleStep(1)

        i = self.measNA
        i.setMaximum(100000000)
        i.setMinimum(0)
        i.setSingleStep(0.1)

        def updateOverlay():
            self.measuredOverlay.x = self.measX.value()
            self.measuredOverlay.y = self.measY.value()
            self.measuredOverlay.r = self.measD.value() / 2
            if not self.parentWindow.cameraView.isRunning:
                self.parentWindow.cameraView.refresh()

        def measTarg():
            x, y, r = self.parentWindow.cameraView.fitCoords
            self._measCenter = (x, y)
            self.measD.setValue(r*2)
            self.measX.setValue(x)
            self.measY.setValue(y)
            updateOverlay()
        self.measureApertureButton.released.connect(measTarg)

        def displayCB():
            if displayCheckbox.checkState():
                self.measuredOverlay.active = True
            else:
                self.measuredOverlay.active = False
            updateOverlay()
        displayCheckbox.stateChanged.connect(displayCB)
        displayCheckbox.setChecked(True)

        gl = QGridLayout()
        gl.addWidget(QLabel("Diameter (px):"), 0, 0)
        gl.addWidget(self.measD, 0, 1)
        gl.addWidget(QLabel("Center (x,y):"), 1, 0)
        gl.addWidget(self.measX, 1, 1)
        gl.addWidget(self.measY, 1, 2)
        gl.addWidget(QLabel("NA"), 2, 0)
        gl.addWidget(self.measNA, 2, 1)
        gl.addWidget(displayCheckbox, 3, 0, 1, 3)
        gl.addWidget(self.measureApertureButton, 4, 0, 1, 3)
        return gl

    def setupTargetPanel(self) -> QGridLayout:
        self.targetD = QDoubleSpinBox(self)
        self.targetNA = QDoubleSpinBox(self)
        self.targetX = QDoubleSpinBox(self)
        self.targetY = QDoubleSpinBox(self)
        self.centerTargetButton = QPushButton("Center to Reference", self)
        displayCheckBox = QCheckBox("Display Overlay", self)
        # configure limits
        for i in [self.targetD, self.targetX, self.targetY]:
            i.setMinimum(0)
            i.setMaximum(100000000)
            i.setSingleStep(1)

        i = self.targetNA
        i.setMaximum(100000000)
        i.setMinimum(0)
        i.setSingleStep(0.1)

        def updateOverlay():
            self.targetOverlay.active = True
            self.targetOverlay.x = self.targetX.value() #self._measCenter[0]
            self.targetOverlay.y = self.targetY.value() #self._measCenter[1]
            self.targetOverlay.r = self.targetD.value() / 2
            if not self.parentWindow.cameraView.isRunning:
                self.parentWindow.cameraView.refresh()
        self.targetY.valueChanged.connect(updateOverlay)
        self.targetX.valueChanged.connect(updateOverlay)

        def targChanged():
            if self._naPerPix != 0:
                self.targetNA.blockSignals(True)
                self.targetNA.setValue(self._naPerPix * self.targetD.value())
                self.targetNA.blockSignals(False)
                updateOverlay()
        self.targetD.valueChanged.connect(targChanged)

        def naChanged():
            if self._naPerPix != 0:
                self.targetD.blockSignals(True)
                self.targetD.setValue(self.targetNA.value() / self._naPerPix)
                self.targetD.blockSignals(False)
                updateOverlay()
        self.targetNA.valueChanged.connect(naChanged)

        def centerTarg():
            #Center the target
            self.targetX.setValue(self.objectiveX.value())
            self.targetY.setValue(self.objectiveY.value())
            updateOverlay()
        self.centerTargetButton.released.connect(centerTarg)

        def displayCB():
            if displayCheckBox.checkState():
                self.targetOverlay.active = True
            else:
                self.targetOverlay.active = False
            updateOverlay()
        displayCheckBox.stateChanged.connect(displayCB)
        displayCheckBox.setChecked(True)


        gl = QGridLayout()
        gl.addWidget(QLabel("Diameter (px):"), 0, 0)
        gl.addWidget(self.targetD, 0, 1, 1, 2)
        gl.addWidget(QLabel("Center (x,y):"), 1, 0)
        gl.addWidget(self.targetX, 1, 1)
        gl.addWidget(self.targetY, 1, 2)
        gl.addWidget(QLabel("NA"), 2, 0)
        gl.addWidget(self.targetNA, 2, 1, 1, 2)
        gl.addWidget(displayCheckBox, 3, 0, 1, 3)
        gl.addWidget(self.centerTargetButton, 4, 0, 1, 3)
        return gl



    def __init__(self, parent: Window = None):
        super().__init__(parent)
        self.parentWindow = parent
        self.setFrameShape(QFrame.StyledPanel)

        self._naPerPix = 0
        self._objCenter = (0, 0)
        self._measCenter = (0, 0)

        self.objectiveOverlay = CircleCenterOverlay(QtCore.Qt.NoBrush, QtCore.Qt.blue, 0, 0, 0)
        self.targetOverlay = CircleCenterOverlay(QtCore.Qt.NoBrush, QtCore.Qt.green, 0, 0, 0)
        self.measuredOverlay = CircleCenterOverlay(QtCore.Qt.NoBrush, QtCore.Qt.cyan, 0, 0, 0)
        parent.cameraView.addOverlay(self.objectiveOverlay)
        parent.cameraView.addOverlay(self.targetOverlay)
        parent.cameraView.addOverlay(self.measuredOverlay)

        l = QVBoxLayout()
        l.setAlignment(QtCore.Qt.AlignTop)
        lab = QLabel("Reference:")
        f = lab.font()
        f.setBold(True)
        lab.setFont(f)
        l.addWidget(lab)
        gl = self.setupObjectivePanel()
        l.addLayout(gl)
        lab = QLabel("Target:")
        f = lab.font()
        f.setBold(True)
        lab.setFont(f)
        l.addWidget(lab)
        gl = self.setupTargetPanel()
        l.addLayout(gl)
        lab = QLabel("Measured:")
        f = lab.font()
        f.setBold(True)
        lab.setFont(f)
        l.addWidget(lab)
        gl = self.setupMeasurePanel()
        l.addLayout(gl)
        l.addStretch()  # Causes the bottom of the layout to push the rest upwards
        self.setLayout(l)
