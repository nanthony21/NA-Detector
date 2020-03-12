from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from instrumental.drivers.cameras import Camera
import time
import numpy as np


class CameraManager(QObject):
    exposureChanged = pyqtSignal(float)
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

    def setAutoExposure(self, enabled: bool):
        #self._cam.set_auto_exposure(enabled) The built in autoexposure doesn't seem to work very well
        self._aeEnabled = enabled
        if self._aeTimer.isActive() and (not enabled):
            self._aeTimer.stop()
        elif (not self._aeTimer.isActive()) and enabled:
            self._aeTimer.start()

    def isAutoExposure(self):
        # return self._cam.auto_exposure
        return self._aeEnabled

    def setExposure(self, exp: float):
        self._exposure = exp
        if self.isRunning:
            self.stop_live_video()
            time.sleep(.1)  # This delay helps prevent a hard crash. Still happens sometimes though.
            self.start_live_video() #This is to update the exposure used.
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
            return self._cam.start_live_video(exposure_time=f"{self._exposure} ms")
        except Exception as e: #If the exposure setting string is bad we can get an error here
            print(e)

    def stop_live_video(self):
        self.isRunning = False
        return self._cam.stop_live_video()

    def wait_for_frame(self, **kwargs):
        return self._cam.wait_for_frame(**kwargs)

    def latest_frame(self, **kwargs):
        return self._cam.latest_frame(**kwargs)

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
                    frameReady = self.wait_for_frame(timeout='0 ms') #This essentially steals frames from the display which makes things laggy.
                arr = self.latest_frame()
            else:
                arr = self.grab_image()
            m = np.percentile(arr, 99)
            if m >= 255:
                newExp = self._exposure * 0.9
            elif abs(target - m) > 5:  # Don't do anything if we're within a decent window.
                newExp = self._exposure * target / m
                if newExp > 1000:
                    newExp = 1000  # Don't exceed one seconds`
            else:
                return
            self.setExposure(newExp)
        finally:
            self._aeTimer.start()
