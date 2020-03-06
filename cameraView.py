from queue import Queue
from threading import Thread

import numpy as np
import scipy
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtWidgets import QLabel, QSizePolicy

from analysis import binarizeImage, initialGuessCircle, fitCircle


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
        self.preoptCoords = None
        self.overlayQ = Queue(maxsize=1)
        self.overlayThread = None
        self.displayOverlay = True
        self._displayPreOpt = False
        self._displayBinary = False
        super().__init__(camera)


    def isDisplayBinary(self):
        return self._displayBinary

    def displayBinary(self, binary: bool):
        self._displayBinary = binary

    def isDisplayInitialGuess(self):
        return self._displayPreOpt

    def displayInitialGuess(self, binary: bool):
        self._displayPreOpt = binary

    @staticmethod
    def generateOverlay(q: Queue, im):
        binar = binarizeImage(im)
        x0, y0, r0 = initialGuessCircle(binar)
        x, y, r = fitCircle(binar, x0, y0, r0)
        if not q.empty():
            _ = q.get() #Clear the queue
        q.put(((x0, y0, r0), (x, y, r)), False) #This will raise an exception if the queue doesn't have room

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
            self.preoptCoords, self.fitCoords = self.overlayQ.get()

        if self._displayBinary:
            binary = binarizeImage(im)
            newim = binary.astype(np.uint8) * 255
        else:
            newim = im  # Convert to RGB
        return newim

    def processPixmap(self):
        pm = self.pixmap()
        if self.fitCoords is not None and self.displayOverlay:
            x, y, r = self.fitCoords
            painter = QPainter(pm)
            # painter.setBrush(QtCore.Qt.red) #This is the fill
            painter.setPen(QtCore.Qt.red)
            painter.drawEllipse(x-r, y-r, r*2, r*2)
        if self.preoptCoords is not None and self._displayPreOpt:
            x,y,r = self.preoptCoords
            painter = QPainter(pm)
            painter.setPen(QtCore.Qt.blue)
            painter.drawEllipse(x - r, y - r, r * 2, r * 2)

        self.setPixmap(pm)