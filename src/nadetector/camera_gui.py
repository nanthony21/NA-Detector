# -*- coding: utf-8 -*-
"""
A very simple GUI that uses a CameraView to view live video from a camera.
"""
from __future__ import annotations
import sys

from PyQt5.QtWidgets import (QApplication)

import os

from .hardware.cameraManager import CameraManager
from .mainWindow import Window
from .widgets.cameraView import CircleOverlayCameraView



class App(QApplication):
    def __init__(self, argv, camera):
        super().__init__(argv)
        self.cameraManager = CameraManager(camera, self)
        self.camview = CircleOverlayCameraView(self.cameraManager)
        self.window = Window(self.camview, self.cameraManager)
        self.window.show()



        
