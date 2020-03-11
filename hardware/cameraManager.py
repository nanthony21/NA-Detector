from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from instrumental.drivers.cameras import Camera

from widgets.cameraView import CameraView
import numpy as np


class CameraManager(QObject):
    autoExposureChanged = pyqtSignal(float)
    def __init__(self, camera: Camera, parent: QObject = None):
        super().__init__(parent)
        self._cam = camera
        self._exposure = 0
        self.isRunning = False
        # self._aeTimer = QTimer()
        # self._aeTimer.setSingleShot(False)
        # self._aeTimer.setInterval(100)  # This is in milliseconds
        # self._aeTimer.timeout.connect(self._runAutoExpose)

    def setAutoExposure(self, enabled: bool):
        self._cam.set_auto_exposure(enabled)
        # if self._aeTimer.isActive() and (not enabled):
            # self._aeTimer.stop()
        # elif (not self._aeTimer.isActive()) and enabled:
            # self._aeTimer.start()

    def isAutoExposure(self):
        return self._cam.auto_exposure()

    def setExposure(self, exp: float):
        self._exposure = exp
        if self.isRunning:
            self.stop_live_video()
            self.start_live_video() #This is to update the exposure used.

    def grab_image(self):
        return self._cam.grab_image(exposure_time=f"{self._exposure} ms")

    def start_live_video(self):
        self.isRunning = True
        return self._cam.start_live_video(exposure_time=f"{self._exposure} ms")

    def stop_live_video(self):
        self.isRunning = False
        return self._cam.stop_live_video()

    def wait_for_frame(self):
        return self._cam.wait_for_frame()

    def latest_frame(self):
        return self._cam.latest_frame()

    @property
    def width(self):
        return self._cam.width

    @property
    def height(self):
        return self._cam.height

    # def _runAutoExpose(self):
    #     arr = self._getImg()
    #     m = np.percentile(arr, 99)
    #     self.autoExposureChanged.emit(1)

    # def _getImg(self):
    #     if self._camView.isRunning:
    #         return self._camView.arr
    #     else:
    #         return self._cam.grab_image()
