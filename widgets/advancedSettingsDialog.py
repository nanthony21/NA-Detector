from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QWidget, QCheckBox, QVBoxLayout, QComboBox

from constants import Methods
from widgets.cameraView import CircleOverlayCameraView


class AdvancedSettingsDialog(QDialog):
    def __init__(self, parent: QWidget, camview: CircleOverlayCameraView):
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings")
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowCloseButtonHint) #Get rid of the close button. this is handled by the selector widget active status

        self.viewBinary = QCheckBox("View Binary Image:", self)
        self.viewBinary.setLayoutDirection(QtCore.Qt.RightToLeft)  # Put label on left side of box
        def setBinary():
            camview.displayPreProcessed = self.viewBinary.isChecked()
        self.viewBinary.stateChanged.connect(setBinary)
        self.viewBinary.setChecked(camview.displayPreProcessed)

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
        layout.addWidget(self.viewBinary)
        layout.addWidget(self.viewPreOpt)
        layout.addWidget(self.methodCombo)
        self.setLayout(layout)