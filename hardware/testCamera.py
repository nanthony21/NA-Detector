import random

import numpy as np
import skimage


class TestCamera:
    def __init__(self, shape, noiseLevel, ring = False):
        self._started = False
        self.noiseLevel = noiseLevel
        self.arrayShape = shape
        self.ring = ring

    def grab_image(self, **kwargs):
        return self._getFrame(self.ring)

    def start_live_video(self, **kwargs):
        self._started = True

    def stop_live_video(self):
        self._started = False

    def wait_for_frame(self, **kwargs):
        return self._started

    def latest_frame(self, **kwargs):
        return self._getFrame(self.ring)

    def set_auto_exposure(self, enable=True):
        pass

    @property
    def auto_exposure(self) -> bool:
        return False

    def _getFrame(self, ring = False):
        y = random.randrange(self.arrayShape[0]//4, self.arrayShape[0]//2)
        x = random.randrange(self.arrayShape[1]//4, self.arrayShape[1]//2)
        r = random.randrange(50, 200)

        coords = skimage.draw.circle(y, x, r, shape=self.arrayShape)
        im = np.zeros(self.arrayShape, dtype=np.uint8)
        im[coords] = 127
        im += (np.random.rand(*self.arrayShape) * self.noiseLevel).astype(np.uint8)

        if ring:
            littleR = r * 0.5
            coords = skimage.draw.circle(y, x, littleR, shape=self.arrayShape)
            im[coords] = 0

        return im

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def width(self):
        return self.arrayShape[1]

    @property
    def height(self):
        return self.arrayShape[0]