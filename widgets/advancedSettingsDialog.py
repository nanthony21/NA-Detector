from __future__ import annotations
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDialog, QWidget, QCheckBox, QVBoxLayout, QComboBox, QTabWidget, QDoubleSpinBox, QGridLayout, QLabel
from constants import Methods
import typing
if typing.TYPE_CHECKING:
    from hardware.cameraManager import CameraManager
    from widgets.cameraView import CircleOverlayCameraView


class AdvancedSettingsDialog(QDialog): #TODO camera exposure (autoexposure), method specific settings (thresholding)
    def __init__(self, parent: QWidget, camview: CircleOverlayCameraView, camManager: CameraManager):
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings")
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint)

        tab = QTabWidget(self)

        self.debugTab = DebugTab(tab, camview)
        self.cameraTab = CameraTab(tab, camManager)
        self.thresholdTab = ThresholdTab(tab)

        tab.addTab(self.cameraTab, "Camera")
        tab.addTab(self.thresholdTab, "Threshold")
        tab.addTab(self.debugTab, "Debug")

        l = QGridLayout()
        l.addWidget(tab, 0, 0)
        self.setLayout(l)

    def show(self):
        super().show()
        self.setFixedSize(self.size())


class CameraTab(QWidget):
    def __init__(self, parent: QWidget, camManager: CameraManager):
        super().__init__(parent)

        self.autoExposeCB = QCheckBox("Auto Exposure", self)
        self.autoExposeCB.setChecked(camManager.isAutoExposure())
        self.exposure = QDoubleSpinBox(self)

        self.expChangeDebounce = QTimer(self)
        self.expChangeDebounce.setSingleShot(True)
        self.expChangeDebounce.setInterval(300)
        def setExposure():
            camManager.setExposure(self.exposure.value())
        self.expChangeDebounce.timeout.connect(setExposure)

        self.exposure.setMinimum(0)
        self.exposure.setMaximum(1000)
        self.exposure.setSingleStep(1)
        self.exposure.setValue(camManager.getExposure())

        def autoExposeChanged():
            ae = self.autoExposeCB.isChecked()
            camManager.setAutoExposure(ae)
            self.exposure.setEnabled(not ae)
            if not ae:
                setExposure()
        self.autoExposeCB.stateChanged.connect(autoExposeChanged)

        def expChanged():
            self.expChangeDebounce.start()
        self.exposure.valueChanged.connect(expChanged)

        def updateExpField(newExp: float):
            self.exposure.blockSignals(True)
            self.exposure.setValue(newExp)
            self.exposure.blockSignals(False)
        camManager.exposureChanged.connect(updateExpField)

        l = QGridLayout()
        l.addWidget(self.autoExposeCB, 0, 0, 1, 2)
        l.addWidget(QLabel("Exposure (ms):"), 1, 0)
        l.addWidget(self.exposure, 1, 1)
        self.setLayout(l)


class ThresholdTab(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        l = QGridLayout()
        self.setLayout(l)


class DebugTab(QWidget):
    def __init__(self, parent: QWidget, camview: CircleOverlayCameraView):
        super().__init__(parent)

        self.viewPreprocessed = QCheckBox("View Background Image:", self)
        self.viewPreprocessed.setLayoutDirection(QtCore.Qt.RightToLeft)  # Put label on left side of box
        def setBinary():
            camview.displayPreProcessed = self.viewPreprocessed.isChecked()
        self.viewPreprocessed.stateChanged.connect(setBinary)
        self.viewPreprocessed.setChecked(camview.displayPreProcessed)

        self.viewPreOpt = QCheckBox("View initial guess:", self)
        self.viewPreOpt.setLayoutDirection(QtCore.Qt.RightToLeft)  # Put label on left side of box
        def viewPreOpt():
            camview.preOptFitOverlay.active = self.viewPreOpt.isChecked()
        self.viewPreOpt.stateChanged.connect(viewPreOpt)
        self.viewPreOpt.setChecked(camview.preOptFitOverlay.active)

        self.methodCombo = QComboBox(self)
        for i in Methods:
            self.methodCombo.addItem(i.name, i)
        self.methodCombo.setCurrentText(camview.method.name)
        def methchanged():
            camview.method = self.methodCombo.currentData()
        self.methodCombo.currentIndexChanged.connect(methchanged)

        layout = QVBoxLayout()
        layout.addWidget(self.viewPreprocessed)
        layout.addWidget(self.viewPreOpt)
        layout.addWidget(self.methodCombo)
        self.setLayout(layout)
