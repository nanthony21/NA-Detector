# -*- coding: utf-8 -*-
"""
A very simple GUI that uses a CameraView to view live video from a camera.
"""
from __future__ import annotations
import sys

from PyQt5.QtWidgets import (QApplication)
from instrumental import instrument, list_instruments

import os

from hardware.cameraManager import CameraManager
from mainWindow import Window
from widgets.cameraView import CircleOverlayCameraView
from hardware.testCamera import TestCamera

os.environ['PATH'] += os.path.abspath('lib') #This makes is so that the Camera driver DLL can be found.


class App(QApplication):
    def __init__(self, argv, camera):
        super().__init__(argv)
        self.cameraManager = CameraManager(camera, self)
        self.camview = CircleOverlayCameraView(self.cameraManager)
        self.window = Window(self.camview, self.cameraManager)
        self.window.show()


if __name__ == '__main__':
    test = False


    def tracefunc(frame, event, arg, indent=[0]):
        if event == "call":
            indent[0] += 2
            print("-" * indent[0] + "> call function", frame.f_code.co_name)
        elif event == "return":
            print("<" + "-" * indent[0], "exit function", frame.f_code.co_name)
            indent[0] -= 2
        return tracefunc

    import sys




    cam = None
    if test:
        cam = TestCamera((512, 1024), 10, ring=True)
    else:
        inst = list_instruments()
        print(f"Found {len(inst)} cameras:")
        print(inst)
        if len(inst) > 0:
            cam = instrument(list_instruments()[0])  # Replace with your camera's alias

    if cam is not None:
        with cam:
            app = App(sys.argv, cam)
            #Initial settings for the app
            app.window.videoButton.click()  # Start the video
            app.window.advancedDlg.cameraTab.autoExposeCB.click() #Turn on autoexposure
            # sys.setprofile(tracefunc)

            app.exec_()
        
