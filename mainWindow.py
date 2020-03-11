from __future__ import annotations
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QGridLayout, QHBoxLayout

from hardware.cameraManager import CameraManager
from widgets.advancedSettingsDialog import AdvancedSettingsDialog
from widgets.aspectRatioWidget import AspectRatioWidget
from widgets.fittingWidget import FittingWidget
import typing
if typing.TYPE_CHECKING:
    from widgets.cameraView import CircleOverlayCameraView


class Window(QMainWindow):
    def __init__(self, camview: CircleOverlayCameraView, camManager: CameraManager):
        super().__init__()
        self.setWindowTitle("NA Detector")
        self.advancedDlg = AdvancedSettingsDialog(self, camview, camManager)
        self.cameraView = camview

        self.button = QPushButton("Start Video")
        self.btn_grab = QPushButton("Grab Frame")
        self.advancedButton = QPushButton("Advanced...")

        self.arWidget = AspectRatioWidget(camview.arr.shape[1] / camview.arr.shape[0], self)
        self.arWidget.setLayout(QVBoxLayout())
        self.arWidget.layout().setContentsMargins(0, 0, 0, 0)
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
        l: QGridLayout = main_area.layout()
        l.addWidget(self.arWidget, 0, 0)
        l.addWidget(button_area, 1, 0)
        l.addWidget(fittingWidget, 0, 1, 2, 1)
        l.setRowStretch(0, 1)
        # l.setHorizontalSpacing(1)
        # l.setVerticalSpacing(1)


        l = button_area.layout()
        l.addStretch()  # Makes the buttons move over rather than spread out.
        l.addWidget(self.button)
        l.addWidget(self.btn_grab)
        l.addWidget(self.advancedButton)

        # Attach some child widgets directly
        self.setCentralWidget(main_area)