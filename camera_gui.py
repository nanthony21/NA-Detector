# -*- coding: utf-8 -*-
# Copyright 2015-2017 Nate Bogdanowicz
"""
A very simple GUI that uses a CameraView to view live video from a camera.
"""
from __future__ import annotations
import sys

from PyQt5 import QtGui
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QScrollArea, QPushButton,
                             QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QWIDGETSIZE_MAX)
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
        

        # self.scroll_area = QScrollArea()
        self.button = QPushButton("Start Video")
        self.btn_grab = QPushButton("Grab Frame")
        
        # self.scroll_area.setWidget(camview)
        self.arWidget = AspectRatioWidget(camview.arr.shape[1]/camview.arr.shape[0], self)
        self.arWidget.setLayout(QVBoxLayout())
        self.arWidget.layout().addWidget(camview)

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

        main_area = QWidget()
        button_area = QWidget()


        # Fill Layouts
        vbox.addWidget(self.arWidget)#self.scroll_area)
        vbox.addWidget(button_area)
        vbox.setStretch(0, 1)
        vbox.setStretch(1,0)
        hbox.addStretch()
        hbox.addWidget(self.button)
        hbox.addWidget(self.btn_grab)
    
        # Assign layouts to widgets
        main_area.setLayout(vbox)
        button_area.setLayout(hbox)
        # self.scroll_area.setLayout(QVBoxLayout())
    
        # Attach some child widgets directly
        self.setCentralWidget(main_area)


class CameraView(QLabel):
    def __init__(self, camera):
        super(CameraView, self).__init__()
        self.camera = camera
        self._cmin = 0
        self._cmax = None
        self.setScaledContents(True)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self.timer = QTimer()
        self.timer.timeout.connect(self._wait_for_frame)

        self.arr = None
        self.grab_image()

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        a = 1

    def grab_image(self):
        self.arr = self.camera.grab_image()
        self._set_pixmap_from_array(self.arr)

    def start_video(self):
        self.camera.start_live_video()
        self.timer.start(0)  # Run full throttle

    def stop_video(self):
        self.timer.stop()
        self.camera.stop_live_video()

    def _set_pixmap_from_array(self, arr):
        bpl = arr.strides[0]
        is_rgb = len(arr.shape) == 3

        if is_rgb:
            if arr.dtype == np.uint8:
                fmt = QImage.Format_RGB32
            elif arr.dtype == np.uint16:
                if not self._cmax:
                    self._cmax = arr.max()  # Set cmax once from first image
                arr = scipy.misc.bytescale(arr, self._cmin, self._cmax)
                fmt = QImage.Format_Indexed8
            else:
                raise Exception("Unsupported color mode")
        else:
            if arr.dtype == np.uint8:
                fmt = QImage.Format_Indexed8
            else:
                raise Exception("Unsupported color mode")
        self._saved_img = arr  # Save a reference to keep Qt from crashing
        image = QImage(arr.data, self.camera.width, self.camera.height, bpl, fmt)

        self.setPixmap(QPixmap.fromImage(image))

    def _wait_for_frame(self):
        frame_ready = self.camera.wait_for_frame(timeout='0 ms')
        if frame_ready:
            self.arr = self.camera.latest_frame(copy=False)
            self._set_pixmap_from_array(self.arr)

    # def set_height(self, h):
    #     """ Sets the height while keeping the image aspect ratio fixed """
    #     cam = self.camera
    #     self.setFixedSize(cam.width*h/cam.height, h)
    #
    # def set_width(self, w):
    #     """ Sets the width while keeping the image aspect ratio fixed """
    #     cam = self.camera
    #     self.setFixedSize(w, cam.height*w/cam.width)

# class CircleOverlayCameraView(CameraView):


class AspectRatioWidget(QWidget):
    def __init__(self, aspect: float, parent: QWidget = None):
        super().__init__(parent)
        self._aspect = aspect

    def resizeEvent(self, event: QtGui.QResizeEvent):
        w, h = event.size().width(), event.size().height()
        self._resize(w, h)

    def _resize(self, width, height):
        newHeight = width / self._aspect #The ideal height based on the new commanded width
        newWidth = height * self._aspect #the ideal width based on the new commanded height
        #Now determine which of the new dimensions to use.
        if width > newWidth:
            self.setMaximumWidth(newWidth)
            self.setMaximumHeight(QWIDGETSIZE_MAX)
        else:
            self.setMaximumHeight(newHeight)
            self.setMaximumWidth(QWIDGETSIZE_MAX)

    def setAspect(self, aspect: float):
        self._aspect = aspect
        self._resize(self.width(), self.height())

if __name__ == '__main__':
    inst = list_instruments()
    print(f"Found {len(inst)} cameras:")
    print(inst)
    if len(inst) > 0:
        cam = instrument(list_instruments()[0])  # Replace with your camera's alias

        with cam:
            app = App(sys.argv, cam)
            app.exec_()
        
