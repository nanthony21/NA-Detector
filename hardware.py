import random

import skimage
import numpy as np


class TestCamera:
    def __init__(self, shape, noiseLevel):
        self._started = False
        self.noiseLevel = noiseLevel
        self.arrayShape = shape

    def grab_image(self):
        return self._getFrame()

    def start_live_video(self):
        self._started = True

    def stop_live_video(self):
        self._started = False

    def wait_for_frame(self, **kwargs):
        return self._started

    def latest_frame(self, **kwargs):
        return self._getFrame()

    def _getFrame(self):
        y = random.randrange(self.arrayShape[0]//4, self.arrayShape[0]//2)
        x = random.randrange(self.arrayShape[1]//4, self.arrayShape[1]//2)
        r = 200

        coords = skimage.draw.circle(y, x, r, shape=self.arrayShape)
        im = np.zeros(self.arrayShape, dtype=np.uint8)
        im[coords] = 127
        im += (np.random.rand(*self.arrayShape) * self.noiseLevel).astype(np.uint8)
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
