from __future__ import annotations
from dataclasses import dataclass
from queue import Queue
from threading import Thread
from typing import List

import numpy as np
import scipy
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QBrush
from PyQt5.QtWidgets import QLabel, QSizePolicy

from abc import ABC, abstractmethod
from analysis import binarizeImage, initialGuessCircle, fitCircle, fitCircleHough, detectEdges
from constants import Methods


class CameraView(QLabel):
    def __init__(self, camera):
        super(CameraView, self).__init__()
        self.camera = camera
        self._cmin = 0
        self._cmax = None
        self.setScaledContents(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(50,50)
        self.timer = QTimer()
        self.timer.timeout.connect(self._wait_for_frame)
        self.isRunning = False
        self.arr = None
        self.grab_image()


    def refresh(self):
        self._set_pixmap_from_array(self.arr)
        self.processPixmap()

    def processImage(self, im: np.ndarray, **kwargs) -> np.ndarray:
        return im  # This class is to be overridden by inheriting classes.

    def grab_image(self):
        self.arr = self.camera.grab_image()
        self.arr = self.processImage(self.arr, block=True)
        self._set_pixmap_from_array(self.arr)
        self.processPixmap()

    def start_video(self):
        self.isRunning = True
        self.camera.start_live_video()
        self.timer.start(0)  # Run full throttle

    def stop_video(self):
        self.isRunning = False
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
        self.preoptCoords = None
        self.fitQ = Queue(maxsize=1)
        self.fitThread = None
        self.displayPreProcessed = False
        self.fitOverlay = CircleCenterOverlay(QtCore.Qt.NoBrush, QtCore.Qt.red, 0, 0, 0)
        self.preOptFitOverlay = CircleCenterOverlay(QtCore.Qt.NoBrush, QtCore.Qt.darkBlue, 0, 0, 0)
        self.fitOverlay.active = True

        self.method = Methods.Minimization

        self._overlays: List[Overlay] = [self.fitOverlay, self.preOptFitOverlay]
        super().__init__(camera)

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        x, y = ev.x(), ev.y()
        pm = self.pixmap()
        scale = self.width()/pm.width() #We assume the height scaling is the same.
        print(scale)
        print(x, y)
        x /= scale
        y /= scale
        ov = CircleOverlay(QtCore.Qt.NoBrush, QtCore.Qt.red, x, y, 1)
        ov.active = True
        self.graphicsProxyWidget()
        self.addOverlay(ov)

    def measureCircle(self, q: Queue, im):
        if self.method == Methods.Minimization:
            binar = binarizeImage(im)
            x0, y0, r0 = initialGuessCircle(binar)
            x, y, r = fitCircle(binar, x0, y0, r0)
        elif self.method == Methods.HoughTransform:
            edges = detectEdges(im)
            x, y, r = fitCircleHough(edges)
            x0, y0, r0 = x, y, r # We don't have an initial guess in this case
        else:
            raise ValueError("No recognized method")
        if not q.empty():
            _ = q.get()  # Clear the queue
        q.put(((x0, y0, r0), (x, y, r)), False)  # This will raise an exception if the queue doesn't have room

    def processImage(self, im: np.ndarray, block=False) -> np.ndarray:
        if self.fitThread is None:
            self.fitThread = Thread(target=self.measureCircle, args=(self.fitQ, im))
            self.fitThread.start()
        else:
            if not self.fitThread.is_alive():
                self.fitThread = Thread(target=self.measureCircle, args=(self.fitQ, im))
                self.fitThread.start()

        if block:
            self.fitThread.join()

        if not self.fitQ.empty():
            self.preoptCoords, self.fitCoords = self.fitQ.get()

        if self.displayPreProcessed:
            if self.method == Methods.Minimization:
                binary = binarizeImage(im)
                newim = binary.astype(np.uint8) * 255
            elif self.method == Methods.HoughTransform:
                edges = detectEdges(im)
                newim = edges.astype(np.uint8) * 255
            else:
                raise ValueError("Unrecognized method")
        else:
            newim = im  # Convert to RGB
        return newim

    def processPixmap(self):
        pm = self.pixmap()
        painter = QPainter(pm)
        if self.fitCoords is not None:
            x, y, r = self.fitCoords
            self.fitOverlay.setCoords(x, y, r)
        if self.preoptCoords is not None:
            x, y, r = self.preoptCoords
            self.preOptFitOverlay.setCoords(x, y, r)
        for overlay in self._overlays:
            if overlay.active:
                overlay.draw(painter)
        self.setPixmap(pm)

    def addOverlay(self, overlay: Overlay):
        self._overlays.append(overlay)

    def removeOverlay(self, overlay: Overlay):
        self._overlays.remove(overlay)

class Overlay(ABC):
    def __init__(self, brush, pen):
        self.brush = brush
        self.pen = pen
        self.active = False

    @abstractmethod
    def draw(self, painter: QPainter):
        pass


class CircleOverlay(Overlay):
    def __init__(self, brush, pen, x, y, r):
        super().__init__(brush, pen)
        self.x = x
        self.y = y
        self.r = r

    def setCoords(self, x, y, r):
        self.x = x
        self.y = y
        self.r = r

    def draw(self, painter):
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawEllipse(self.x-self.r, self.y-self.r, self.r*2, self.r*2)


class CircleCenterOverlay(CircleOverlay):
    def __init__(self, brush, pen, x, y, r):
        super().__init__(brush, pen, x, y, r)
        self.len = 10

    def draw(self, painter):
        super().draw(painter)
        painter.drawLine(self.x-self.len, self.y, self.x+self.len, self.y)
        painter.drawLine(self.x, self.y-self.len, self.x, self.y+self.len)