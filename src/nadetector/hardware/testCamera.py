import random

import numpy as np
import skimage
import typing as t_


class TestCamera:
    def __init__(self, shape: t_.Tuple[int, int], noiseLevel: float, ring: bool = False):
        """
        Simulates a Insturmental-lib camera object.

        Args:
            shape: The shape of the 2d camera image array.
            noiseLevel: The noise present in the image.
            ring: If true then a donut will be drawn rather than a circle.
        """
        self._started = False
        self._noiseLevel = noiseLevel
        self._arrayShape = shape
        self._ring = ring

    def grab_image(self, **kwargs):
        return self._getFrame(self._ring)

    def start_live_video(self, **kwargs):
        self._started = True

    def stop_live_video(self):
        self._started = False

    def wait_for_frame(self, **kwargs):
        return self._started

    def latest_frame(self, **kwargs):
        return self._getFrame(self._ring)

    def set_auto_exposure(self, enable=True):
        pass

    @property
    def auto_exposure(self) -> bool:
        return False

    def _getFrame(self, ring: bool = False) -> np.ndarray:
        """

        Args:
            ring: If true then a donut will be drawn rather than a circle.

        Returns: 2D image array.

        """
        y = random.randrange(self._arrayShape[0] // 4, self._arrayShape[0] // 2)
        x = random.randrange(self._arrayShape[1] // 4, self._arrayShape[1] // 2)
        r = random.randrange(50, 200)

        coords = skimage.draw.circle(y, x, r, shape=self._arrayShape)
        im = np.zeros(self._arrayShape, dtype=np.uint8)
        im[coords] = 127
        im += (np.random.rand(*self._arrayShape) * self._noiseLevel).astype(np.uint8)

        if ring:
            littleR = r * 0.5
            coords = skimage.draw.circle(y, x, littleR, shape=self._arrayShape)
            im[coords] = 0

        return im

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def width(self):
        return self._arrayShape[1]

    @property
    def height(self):
        return self._arrayShape[0]