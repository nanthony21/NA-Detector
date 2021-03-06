from __future__ import annotations
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QMainWindow, QPushButton, QWidget, QGridLayout, QHBoxLayout, QLabel

from nadetector.hardware import CameraManager
from nadetector.widgets import AdvancedSettingsDialog
from nadetector.widgets.fittingWidget import FittingWidget
import typing
from nadetector.widgets.cameraView import ZoomableView
if typing.TYPE_CHECKING:
    from nadetector.widgets.cameraView import CircleOverlayCameraView


class Window(QMainWindow):
    def __init__(self, camview: CircleOverlayCameraView, camManager: CameraManager):
        super().__init__()
        self.setWindowTitle("NA Detector")
        self.advancedDlg = AdvancedSettingsDialog(self, camview, camManager)
        self.cameraView = camview
        self._graphicsView = ZoomableView(camview)

        self.coordsLabel = QLabel(self)
        self.videoButton = QPushButton("Start Video", self)
        self.btn_grab = QPushButton("Grab Frame", self)
        self.advancedButton = QPushButton("Advanced...", self)

        def setCoordLabel(x, y):
            v = self.cameraView.rawArray[y, x]
            self.coordsLabel.setText(f"x={x}, y={y}, value={v}")
        self.cameraView.mouseMoved.connect(setCoordLabel)

        def start_stop():
            if not self.cameraView.isRunning:
                camview.start_video()
                self.videoButton.setText("Stop Video")
                self.btn_grab.setEnabled(False)
            else:
                camview.stop_video()
                self.videoButton.setText("Start Video")
                self.btn_grab.setEnabled(True)
        self.videoButton.clicked.connect(start_stop)

        def grab():
            camview.grab_image()
        self.btn_grab.clicked.connect(grab)

        def showAdvanced():
            self.advancedDlg.show()

            # Move dialog to the top of the "advanced" button
            rect = self.advancedDlg.geometry()
            newPoint = self.advancedButton.mapToGlobal(QPoint(0, -rect.height()))
            rect.moveTo(newPoint)
            self.advancedDlg.setGeometry(rect)

        self.advancedButton.released.connect(showAdvanced)

        main_area = QWidget(self)
        main_area.setLayout(QGridLayout())
        button_area = QWidget()
        button_area.setLayout(QHBoxLayout())
        self.fittingWidget = FittingWidget(self)

        # Fill Layouts
        l: QGridLayout = main_area.layout()
        l.addWidget(self._graphicsView, 0, 0)
        l.addWidget(button_area, 1, 0)
        l.addWidget(self.fittingWidget, 0, 1, 2, 1)
        l.setRowStretch(0, 1)

        l = button_area.layout()
        l.addStretch()  # Makes the buttons move over rather than spread out.
        l.addWidget(self.coordsLabel)
        l.addWidget(self.videoButton)
        l.addWidget(self.btn_grab)
        l.addWidget(self.advancedButton)

        # Attach some child widgets directly
        self.setCentralWidget(main_area)

    def getSettings(self) -> dict:
        return self.fittingWidget.getSetting()

    def loadSettings(self, settings: dict):
        self.fittingWidget.loadFromSettings(settings)
