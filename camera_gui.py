# -*- coding: utf-8 -*-
# Copyright 2015-2017 Nate Bogdanowicz
"""
A very simple GUI that uses a CameraView to view live video from a camera.
"""
from __future__ import annotations
import sys

from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton,
                             QVBoxLayout, QHBoxLayout, QGridLayout)
from instrumental import instrument, list_instruments

import os

from widgets.cameraView import CircleOverlayCameraView
from hardware import TestCamera
from widgets.aspectRatioWidget import AspectRatioWidget
from widgets.advancedSettingsDialog import AdvancedSettingsDialog
from widgets.fittingWidget import FittingWidget

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
        self.advancedDlg = AdvancedSettingsDialog(self, camview)
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
        
