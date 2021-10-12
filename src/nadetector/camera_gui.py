# -*- coding: utf-8 -*-
"""
A very simple GUI that uses a CameraView to view live video from a camera.
"""
from __future__ import annotations
import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication)

import os

from .hardware.cameraManager import CameraManager
from .mainWindow import Window
from .widgets.cameraView import CircleOverlayCameraView


class App(QApplication):
    def __init__(self, argv, camera):
        super().__init__(argv)

        self.aboutToQuit.connect(self.onQuit)

        self.cameraManager = CameraManager(camera, self)
        self.camview = CircleOverlayCameraView(self.cameraManager)
        self.window = Window(self.camview, self.cameraManager)

        settings = QtCore.QSettings("BackmanLab", "NADetector")
        self.window.loadSettings(settings.value("windowSettings", defaultValue={'targetNA': 0.52, 'referenceNA': 1.49}))

        self.window.show()

    def onQuit(self) -> None:
        settings = QtCore.QSettings("BackmanLab", "NADetector")
        settings.setValue("windowSettings", self.window.getSettings())



        
