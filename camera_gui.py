# -*- coding: utf-8 -*-
# Copyright 2015-2017 Nate Bogdanowicz
"""
A very simple GUI that uses a CameraView to view live video from a camera.
"""
from __future__ import annotations
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QScrollArea, QPushButton,
                             QVBoxLayout, QHBoxLayout, QLabel)
from instrumental import instrument, list_instruments
import numpy as np
import scipy

import os

os.environ['PATH'] += os.path.abspath('lib')


class App(QApplication):
    def __init__(self, argv, camera):
        super().__init__(argv)

        self.camera = camera
        self.camview = CameraView(camera)
        self.window = Window(self.camview)
        self.window.show()

        
class Window(QMainWindow):
    def __init__(self, camview: CameraView):
        super().__init__()
        
        main_area = QWidget()
        button_area = QWidget()
        self.scroll_area = QScrollArea()
        self.button = QPushButton("Start Video")
        self.btn_grab = QPushButton("Grab Frame")
        
        self.scroll_area.setWidget(camview)
        
        self.button.running=False
        def start_stop():
            if not self.button.running:
                camview.start_video()
                self.button.setText("Stop Video")
                self.button.running = True
            else:
                camview.stop_video()
                self.button.setText("Start Video")
                self.button.running = False
        self.button.clicked.connect(start_stop)
        
        def grab():
            if not self.button.running:
                camview.grab_image()
        self.btn_grab.clicked.connect(grab)
    
        # Create layouts
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
    
        # Fill Layouts
        vbox.addWidget(self.scroll_area)
        vbox.addWidget(button_area)
        hbox.addStretch()
        hbox.addWidget(self.button)
        hbox.addWidget(self.btn_grab)
    
        # Assign layouts to widgets
        main_area.setLayout(vbox)
        button_area.setLayout(hbox)
        self.scroll_area.setLayout(QVBoxLayout())
    
        # Attach some child widgets directly
        self.setCentralWidget(main_area)


class CameraView(QLabel):
    def __init__(self, camera=None):
        super(CameraView, self).__init__()
        self.camera = camera
        self._cmin = 0
        self._cmax = None

    def grab_image(self):
        arr = self.camera.grab_image()
        self._set_pixmap_from_array(arr)

    def start_video(self):
        timer = QTimer()
        self.timer = timer
        timer.timeout.connect(self._wait_for_frame)
        self.camera.start_live_video()
        timer.start(0)  # Run full throttle

    def stop_video(self):
        self.timer.stop()
        self.camera.stop_live_video()

    def _set_pixmap_from_array(self, arr):
        bpl = arr.strides[0]
        is_rgb = len(arr.shape) == 3

        if is_rgb and arr.dtype == np.uint8:
            format = QImage.Format_RGB32
            image = QImage(arr.data, self.camera.width, self.camera.height, bpl, format)
        elif not is_rgb and arr.dtype == np.uint8:
            # TODO: Somehow need to make sure data is ordered as I'm assuming
            format = QImage.Format_Indexed8
            image = QImage(arr.data, self.camera.width, self.camera.height, bpl, format)
            self._saved_img = arr
        elif not is_rgb and arr.dtype == np.uint16:
            if not self._cmax:
                self._cmax = arr.max()  # Set cmax once from first image
            arr = scipy.misc.bytescale(arr, self._cmin, self._cmax)
            format = QImage.Format_Indexed8
            w, h = self.camera.width, self.camera.height
            image = QImage(arr.data, w, h, w, format)
            self._saved_img = arr  # Save a reference to keep Qt from crashing
        else:
            raise Exception("Unsupported color mode")

        self.setPixmap(QPixmap.fromImage(image))
        pixmap_size = self.pixmap().size()
        if pixmap_size != self.size():
            self.setMinimumSize(self.pixmap().size())

    def _wait_for_frame(self):
        frame_ready = self.camera.wait_for_frame(timeout='0 ms')
        if frame_ready:
            arr = self.camera.latest_frame(copy=False)
            self._set_pixmap_from_array(arr)

    def set_height(self, h):
        """ Sets the height while keeping the image aspect ratio fixed """
        self.setScaledContents(True)
        cam = self.camera
        self.setFixedSize(cam.width*h/cam.height, h)

    def set_width(self, w):
        """ Sets the width while keeping the image aspect ratio fixed """
        self.setScaledContents(True)
        cam = self.camera
        self.setFixedSize(w, cam.height*w/cam.width)

if __name__ == '__main__':
    inst = list_instruments()
    print(f"Found {len(inst)} cameras:")
    print(inst)
    if len(inst) > 0:
        cam = instrument(list_instruments()[0])  # Replace with your camera's alias

        with cam:
            app = App(sys.argv, cam)
            app.exec_()
        
