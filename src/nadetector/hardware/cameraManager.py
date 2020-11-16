from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from instrumental.drivers.cameras import Camera
import time
import os
import numpy as np

# def log(n):
#     def dec(f):
#         def newf(*args, **kwargs):
#             print(n, 'start')
#             f(*args, **kwargs)
#             print(n, 'stop')
#         return newf
#     return dec

class CameraManager(QObject):
    exposureChanged = pyqtSignal(float)
    frameReady = pyqtSignal(np.ndarray)

    def __init__(self, camera: Camera, parent: QObject = None):
        super().__init__(parent)
        self._cam = camera
        self._exposure = 10
        self.isRunning = False
        self._aeEnabled = False
        self._aeTimer = QTimer()
        self._aeTimer.setSingleShot(True)
        self._aeTimer.setInterval(100)  # This is in milliseconds
        self._aeTimer.timeout.connect(self._runAutoExpose)
        self._frameGrabTimer = QTimer()
        self._frameGrabTimer.setSingleShot(False)
        self._frameGrabTimer.setInterval(50)
        self._frameGrabTimer.timeout.connect(self._waitForFrame)

    def _waitForFrame(self):
        ready = self._cam.wait_for_frame(timeout='0 ms')
        if ready and self.isRunning:
            self.frameReady.emit(self._cam.latest_frame())

    def setAutoExposure(self, enabled: bool):
        self._aeEnabled = enabled
        if self._aeTimer.isActive() and (not enabled):
            self._aeTimer.stop()
        elif (not self._aeTimer.isActive()) and enabled:
            self._aeTimer.start()

    def isAutoExposure(self):
        return self._aeEnabled

    def setExposure(self, exp: float):
        oldexp = self._exposure
        self._exposure = exp
        if self.isRunning:
            self.stop_live_video()
#            time.sleep(oldexp/1000 + 0.1)  # This delay helps prevent a hard crash. Still happens sometimes though. Makes things laggy during autoexposure
            self.start_live_video()  # This is to update the exposure used.
        self.exposureChanged.emit(self._exposure)

    def getExposure(self):
        return self._exposure

    def grab_image(self):
        try:
            return self._cam.grab_image(exposure_time=f"{self._exposure} ms")
        except Exception as e:  # If the exposure setting string is bad we can get an eror here
            print(e)

    def start_live_video(self):
        self.isRunning = True
        try:
            self._cam.start_live_video(exposure_time=f"{self._exposure} ms")
            self._frameGrabTimer.start()
        except Exception as e: #If the exposure setting string is bad we can get an error here
            print(e)

    def stop_live_video(self):
        self.isRunning = False
        self._frameGrabTimer.stop()
        self._cam.stop_live_video()

    @property
    def width(self):
        return self._cam.width

    @property
    def height(self):
        return self._cam.height

    def _runAutoExpose(self):
        try:
            target = 250  # Assuming a max of 255
            if self.isRunning:
                frameReady = False # We have to get a fresh frame to make sure it's actually at the correct exposure.
                while not frameReady:
                    frameReady = self._cam.wait_for_frame(timeout='0 ms')
                arr = self._cam.latest_frame(copy=True)
                self.frameReady.emit(arr)
            else:
                arr = self.grab_image()
            if arr is None:
                return  # This can sometime happen when the video is stopped.
            m = np.percentile(arr, 99.7)
            if m >= 255:
                newExp = self._exposure * 0.8
            elif abs(target - m) > 5:  # Don't do anything if we're within a decent window.
                newExp = self._exposure * target / m
                if newExp > 1000:
                    newExp = 1000  # Don't exceed one seconds`
            else:
                return
            self.setExposure(newExp)
        finally:
            self._aeTimer.start()
