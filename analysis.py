# -*- coding: utf-8 -*-
"""
Created on Thu May 30 09:56:28 2019

@author: backman05
"""
import skimage as sk
from typing import Tuple
import numpy as np
import scipy as sp


def fitCircle(im: np.ndarray) -> Tuple[float, float, float]:
#    thresh = sk.filters.threshold_otsu(im) This wasn't always working well
    thresh = sk.filters.threshold_li(im)
    binar = im > thresh
    regions = sk.measure.regionprops(binar.astype(np.uint8))
    bubble = regions[0] #this will be the largest detected region.
    y0, x0 = bubble.centroid
    r0 = bubble.major_axis_length / 2 #These are our initial values that we will start our optimization with.
            
    def cost(args: (float, float, float)): #We have to use args here rather than individual arguments because of out the sp.optimize function works. the binarized image is included in the function using closure.
        """Calculate the cost to be minimized which in this case is the negative of the number of pixels that overlap between our circle(x,y,r) and the binary image."""
        x, y, r = args
        coords = sk.draw.circle(y, x, r, shape=binar.shape)
        template = np.zeros_like(binar)
        template[coords] = True
        return -(np.sum(template == binar))
    
    X, Y, R = sp.optimize.fmin(cost, (x0, y0, r0))
    return X, Y, R