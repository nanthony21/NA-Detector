# -*- coding: utf-8 -*-
# Copyright 2015-2017 Nate Bogdanowicz
"""
A very simple GUI that uses a CameraView to view live video from a camera.
"""
from __future__ import annotations
import sys

from PyQt5.QtWidgets import (QApplication)
from instrumental import instrument, list_instruments

import os

from mainWindow import Window
from widgets.cameraView import CircleOverlayCameraView
from hardware import TestCamera

os.environ['PATH'] += os.path.abspath('lib') #This makes is so that the Camera driver DLL can be found.


class App(QApplication):
    def __init__(self, argv, camera):
        super().__init__(argv)
        self.camera = camera
        self.camview = CircleOverlayCameraView(camera)
        self.window = Window(self.camview)
        self.window.show()


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
        
