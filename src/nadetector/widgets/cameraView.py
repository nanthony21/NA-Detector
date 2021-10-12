from __future__ import annotations
from queue import Queue
from threading import Thread
from typing import List

import numpy as np
import scipy
import skimage
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QBrush, QColor
from PyQt5.QtWidgets import QLabel, QSizePolicy, QGraphicsView, QGraphicsScene

from abc import ABC, abstractmethod

from skimage.transform import downscale_local_mean

from nadetector.analysis import binarizeImageLi, binarizeImageOtsu, initialGuessCircle, fitCircle, fitCircleHough, detectEdges
from nadetector.constants import Methods
import typing
if typing.TYPE_CHECKING:
    from nadetector.hardware import CameraManager


class ZoomableView(QGraphicsView):
    """This is a version of QGraphicsView that takes a Qt FigureCanvas from matplotlib and automatically resized the
    canvas to fill as much of the view as possible. A debounce timer is used to prevent lag due to attempting the resize
    the canvas too quickly. This allows for relatively smooth operation. This is essential for us to include a matplotlib
    plot that can maintain it's aspect ratio within a Qt layout.

    Args:
        plot: A matplotlib FigureCanvas that is compatible with Qt (FigureCanvasQT or FigureCanvasQTAgg)

    """
    def __init__(self, imageView: CameraView):
        super().__init__()
        scene = QGraphicsScene(self)
        scene.addWidget(imageView)
        self.setScene(scene)
        self._scaleFactor = 1

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """
        Scale the view on mouse scroll
        """
        scaleFactor = 1 + (event.angleDelta().y() / 600)
        # Limit zoom to a reasonable range.
        if scaleFactor > 1 and self._scaleFactor > 10:
            return
        elif scaleFactor < 1 and self._scaleFactor < .8:
            return
        self.scale(scaleFactor, scaleFactor)
        self._scaleFactor = self._scaleFactor * scaleFactor  #  Keep track of current scaling factor


    # def _resizePlot(self):
    #     """This method is indirectly called by the resizeEvent through the debounce timer and sets the size of the plot
    #     to maximize its size without changing aspect ratio."""
    #     w, h = self.size().width(), self.size().height()
    #     r = self.scene().sceneRect()
    #     s = min([w, h])  # Get the side length of the biggest square that can fit within the rectangle view area.
    #     self.plot.resize(s, s)  # Set the plot to the size of the square that fits in view.
    #     r.setSize(QSizeF(s, s))
    #     self.scene().setSceneRect(r)  # Set the scene size to the square that fits in view.
    #
    # def resizeEvent(self, event: QtGui.QResizeEvent):
    #     """Every time that the view is resized this event will fire and start the debounce timer. The timer will only
    #     actually time out if this event doesn't restart it within the timeout period."""
    #     self._debounce.start()
    #     super().resizeEvent(event)
    #


class CameraView(QLabel):
    def __init__(self, camera: CameraManager):
        super(CameraView, self).__init__()
        self.camera = camera
        self._cmin = 0
        self._cmax = None
        self.setScaledContents(True)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setMinimumSize(50,50)
        self.camera.frameReady.connect(self._displayNewFrame)
        self.isRunning = False
        self.rawArray = None
        self.processedArray = None
        self.grab_image(withProcessing=False)

    def refresh(self):
        self._set_pixmap_from_array(self.processedArray)
        self.processPixmap()

    def processImage(self, im: np.ndarray, **kwargs) -> np.ndarray:
        return im  # This class is to be overridden by inheriting classes.

    def grab_image(self, withProcessing=True):
        self.rawArray = self.camera.grab_image()
        if withProcessing:
            self.processedArray = self.processImage(self.rawArray, block=True)
        else:
            self.processedArray = self.rawArray
        self._set_pixmap_from_array(self.processedArray)
        self.processPixmap()

    def start_video(self):
        self.isRunning = True
        self.camera.start_live_video()

    def stop_video(self):
        self.isRunning = False
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
        self._saved_img = arr  # Save a reference to keep Qt from crashing. I don't think this is necessary
        image = QImage(arr.data, arr.shape[1], arr.shape[0], bpl, fmt)
        pm = QPixmap.fromImage(image)
        self.setPixmap(pm)

    def _displayNewFrame(self, frame):
        self.camera.frameReady.disconnect(self._displayNewFrame)
        self.rawArray = frame.copy()
        self.processedArray = self.processImage(self.rawArray, block=False)
        self._set_pixmap_from_array(self.processedArray)
        self.processPixmap()
        self.camera.frameReady.connect(self._displayNewFrame)


    def processPixmap(self):
        pass


class CircleOverlayCameraView(CameraView):
    mouseMoved = pyqtSignal(int, int)
    fitCompleted = pyqtSignal(float, float, float)

    def __init__(self, camera):
        self.fitCoords = None
        self.preoptCoords = None
        self.fitQ = Queue(maxsize=1)
        self.fitThread = None
        self.displayPreProcessed = False
        self.preOptFitOverlay = CircleCenterOverlay(QtCore.Qt.NoBrush, QtCore.Qt.red, 0, 0, 0)  # An overlay used for debug purposes to see the initial guess of the aperture circle before optimization.

        self._downSample = 1
        self.method = Methods.LiMinimization

        self._overlays: List[Overlay] = [self.preOptFitOverlay]
        super().__init__(camera)
        self.setMouseTracking(True) #Makes mouseMoveEventFire without clicking.

    def _mapWidgetCoordToPixel(self, x, y):
        pm = self.pixmap()
        scale = self.width()/pm.width() #We assume the height scaling is the same.
        x /= scale
        y /= scale
        if x > self.camera.width:
            x = self.camera.width
            print('errr x')
        if y > self.camera.height:
            y = self.camera.height
            print('errr y')
        return x, y

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        pass
        #Testing purposes only, draw a 1 pixel radius circle at the mouse click.
        # x, y = self._mapWidgetCoordToPixel(ev.x(), ev.y())
        # ov = CircleOverlay(QtCore.Qt.NoBrush, QtCore.Qt.red, x, y, 1)
        # ov.active = True
        # self.addOverlay(ov)

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        x, y = self._mapWidgetCoordToPixel(ev.x(), ev.y())
        self.mouseMoved.emit(x, y)
        super().mouseMoveEvent(ev)

    def measureCircle(self, q: Queue, im):
        if self._downSample != 1:
            dtype = im.dtype
            im = downscale_local_mean(im, (self._downSample, self._downSample)).astype(dtype)
        if self.method == Methods.LiMinimization:
            binar = binarizeImageLi(im)
            x0, y0, r0 = initialGuessCircle(binar)
            x, y, r = fitCircle(binar, x0, y0, r0)
        elif self.method == Methods.OtsuMinimization:
            binar = binarizeImageOtsu(im)
            x0, y0, r0 = initialGuessCircle(binar)
            x, y, r = fitCircle(binar, x0, y0, r0)
        elif self.method == Methods.HoughTransform:
            edges = detectEdges(im)
            x0, y0, r0 = initialGuessCircle(edges)
            x, y, r = fitCircleHough(edges, x0, y0, r0)
        else:
            raise ValueError("No recognized method")
        if self._downSample != 1:
            x0 *= self._downSample; y0 *= self._downSample; r0 *= self._downSample; x *= self._downSample; y *= self._downSample; r *= self._downSample;
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
            self.fitCompleted.emit(*self.fitCoords)

        if self.displayPreProcessed:
            if self.method == Methods.LiMinimization:
                binary = binarizeImageLi(im)
                newim = binary.astype(np.uint8) * 255
            elif self.method == Methods.OtsuMinimization:
                binary = binarizeImageOtsu(im)
                newim = binary.astype(np.uint8) * 255
            elif self.method == Methods.HoughTransform:
                edges = detectEdges(im)
                newim = edges.astype(np.uint8) * 255
            else:
                raise ValueError("Unrecognized method")
        else:
            newim = im
        return newim

    def processPixmap(self):
        pm = self.pixmap()
        painter = QPainter(pm)
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

    def setDownSampling(self, ds: int):
        self._downSample = ds


class Overlay(ABC):
    """
    A base class for an overlay drawn on a QWidget
    """
    def __init__(self, brush: typing.Union[QBrush, QtCore.Qt.BrushStyle], pen: typing.Union[QPen, QtCore.Qt.PenStyle, QColor]):
        self.brush = brush
        self.pen = pen
        self.active = False

    @abstractmethod
    def draw(self, painter: QPainter):
        """Use the painter passed to this method to draw the shape on the QWidget"""
        pass


class CircleOverlay(Overlay):
    """
    A simple circular overlay.

    Args:
        brush: The brush that determines the line style of the overlay.
        pen: The pen that determines the color of the overlay.
        x, y, r: The initial coordinates of the overlaid circle.
    """
    def __init__(self, brush: typing.Union[QBrush, QtCore.Qt.BrushStyle], pen: typing.Union[QPen, QtCore.Qt.PenStyle, QColor], x: float, y: float, r: float):
        super().__init__(brush, pen)
        self.x = x
        self.y = y
        self.r = r

    def setCoords(self, x: float, y: float, r: float):
        """
        Change the coordinates of the overlay.

        Args:
            x: Initial X coord of circle
            y: Initial Y coord of circle
            r: Initial radius of circle
        """
        self.x = x
        self.y = y
        self.r = r

    def draw(self, painter: QPainter):
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawEllipse(self.x-self.r, self.y-self.r, self.r*2, self.r*2)


class CircleCenterOverlay(CircleOverlay):
    """
    A circular overlay with a crosshair at the center.

    Args:
        brush: The brush that determines the line style of the overlay.
        pen: The pen that determines the color of the overlay.
        x, y, r: The initial coordinates of the overlaid circle.
    """
    def __init__(self, brush: typing.Union[QBrush, QtCore.Qt.BrushStyle], pen: typing.Union[QPen, QtCore.Qt.PenStyle, QColor], x: float, y: float, r: float):
        super().__init__(brush, pen, x, y, r)
        self.len = 10  # The length of a single line in the crosshair.

    def draw(self, painter: QPainter):
        super().draw(painter)
        painter.drawLine(self.x-self.len, self.y, self.x+self.len, self.y)
        painter.drawLine(self.x, self.y-self.len, self.x, self.y+self.len)


class RectangleOverlay(Overlay):
    """
    A simple rectangular overlay.

    Args:
        brush: The brush that determines the line style of the overlay.
        pen: The pen that determines the color of the overlay.
        x, y: The initial coordinates of the top left corner of the rectangle.
        w: The width of the rectangle.
        h: The height of the rectangle.
    """
    def __init__(self, brush: typing.Union[QBrush, QtCore.Qt.BrushStyle], pen: typing.Union[QPen, QtCore.Qt.PenStyle, QColor], x: float, y: float, w: float, h: float):
        super().__init__(brush, pen)
        self._x = x
        self._y = y
        self._w = w
        self._h = h

    def setTopLeftCorner(self, x: float, y: float):
        """Move the origin (top left corner) of the rectangle.

        Args:
            x: The x coordinate.
            y: The y coordinate.
        """
        self._x = x
        self._y = y

    def setWidth(self, width: float):
        self._w = width

    def setHeight(self, height: float):
        self._h = height

    def draw(self, painter: QPainter):
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawRect(self._x, self._y, self._w, self._h)
