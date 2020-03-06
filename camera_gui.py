# -*- coding: utf-8 -*-
# Copyright 2015-2017 Nate Bogdanowicz
"""
A very simple GUI that uses a CameraView to view live video from a camera.
"""
from __future__ import annotations
import sys
from queue import Queue
from threading import Thread

import skimage
from PyQt5 import QtGui
from PyQt5  import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QScrollArea, QPushButton,
                             QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QWIDGETSIZE_MAX, QCheckBox)
from instrumental import instrument, list_instruments
import numpy as np
import scipy
from analysis import fitCircle, binarizeImage

import os

from analysis import fitCircleTest
from hardware import TestCamera

os.environ['PATH'] += os.path.abspath('lib')


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
        

        # self.scroll_area = QScrollArea()
        self.button = QPushButton("Start Video")
        self.btn_grab = QPushButton("Grab Frame")
        
        # self.scroll_area.setWidget(camview)
        self.arWidget = AspectRatioWidget(camview.arr.shape[1]/camview.arr.shape[0], self)
        self.arWidget.setLayout(QVBoxLayout())
        self.arWidget.layout().addWidget(camview)

        self.button.running = False
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

        self.viewBinary = QCheckBox("View Binary Image:", self)
        self.viewBinary.stateChanged.connect(lambda: camview.displayBinary(self.viewBinary.isChecked()))
        self.viewBinary.setChecked(camview.isDisplayBinary())
    
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
        hbox.addWidget(self.viewBinary)
    
        # Assign layouts to widgets
        main_area.setLayout(vbox)
        button_area.setLayout(hbox)
        # self.scroll_area.setLayout(QVBoxLayout())
    
        # Attach some child widgets directly
        self.setCentralWidget(main_area)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)


class CameraView(QLabel):
    def __init__(self, camera):
        super(CameraView, self).__init__()
        self.camera = camera
        self._cmin = 0
        self._cmax = None
        self.setScaledContents(True)
        # self.setFixedSize(camera.width, camera.height)
        # self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(50,50)
        self.timer = QTimer()
        self.timer.timeout.connect(self._wait_for_frame)

        self.arr = None
        self.grab_image()


    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        a = 1

    def processImage(self, im: np.ndarray, **kwargs) -> np.ndarray:
        return im #This class is to be overridden by inheriting classes.

    def grab_image(self):
        self.arr = self.camera.grab_image()
        self.arr = self.processImage(self.arr, block=True)
        self._set_pixmap_from_array(self.arr)
        self.processPixmap()

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
                fmt = QImage.Format_RGB888
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
            self.arr = self.processImage(self.arr, block=False)
            self._set_pixmap_from_array(self.arr)
            self.processPixmap()

    def processPixmap(self):
        pass


class CircleOverlayCameraView(CameraView):
    def __init__(self, camera):
        self.fitCoords = None
        self.overlayQ = Queue(maxsize=1)
        self.overlayThread = None
        self.displayOverlay = True
        self._displayBinary = False
        super().__init__(camera)


    def isDisplayBinary(self):
        return self._displayBinary

    def displayBinary(self, binary: bool):
        self._displayBinary = binary

    @staticmethod
    def generateOverlay(q: Queue, im):
        binar = binarizeImage(im)
        x0, y0, r = fitCircle(binar)
        # x = np.linspace(0, im.shape[1]-1, num=im.shape[1]) - x0
        # y = np.linspace(0, im.shape[0]-1, num=im.shape[0]) - y0
        # X, Y = np.meshgrid(x, y)
        # R = np.sqrt(X**2 + Y**2)
        if not q.empty():
            _ = q.get() #Clear the queue
        q.put((x0,y0,r), False) #This will raise an exception if the queue doesn't have room

    def processImage(self, im: np.ndarray, block=False) -> np.ndarray:
        if self.overlayThread is None:
            self.overlayThread = Thread(target=self.generateOverlay, args=(self.overlayQ, im))
            self.overlayThread.start()
        else:
            if not self.overlayThread.is_alive():
                self.overlayThread = Thread(target=self.generateOverlay, args=(self.overlayQ, im))
                self.overlayThread.start()

        if block:
            self.overlayThread.join()

        if not self.overlayQ.empty():
            self.fitCoords = self.overlayQ.get()

        # newim = np.ones((im.shape[0], im.shape[1], 3), dtype=np.uint8)
        if self._displayBinary:
            binary = binarizeImage(im)
            newim = binary.astype(np.uint8) * 255
        else:
            newim = im  # Convert to RGB
        return newim

    def processPixmap(self):
        if self.fitCoords is not None and self.displayOverlay:
            x, y, r = self.fitCoords
            pm = self.pixmap()
            painter = QPainter(pm)
            # painter.setBrush(QtCore.Qt.red) #This is the fill
            painter.setPen(QtCore.Qt.red)
            painter.drawEllipse(x-r, y-r, r*2, r*2)
            self.setPixmap(pm)


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
        
