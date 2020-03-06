# -*- coding: utf-8 -*-
"""
Created on Thu May 30 09:56:28 2019

@author: backman05
"""
import time

import skimage as sk
import skimage.filters as skfilters
from typing import Tuple
import numpy as np
import scipy as sp


def binarizeImage(im: np.ndarray) -> np.ndarray:
    #    thresh = sk.filters.threshold_otsu(im) This wasn't always working well
    thresh = skfilters.threshold_li(im)
    binar = im > thresh
    return binar

def fitCircle(binar: np.ndarray) -> Tuple[float, float, float]:
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
    
    result = sp.optimize.minimize(cost, x0=(x0, y0, r0))
    X, Y, R = tuple(result.x)
    # print(result.success)
    # print(X,Y,R)
    return X, Y, R


def fitCircleTest(im: np.ndarray) -> Tuple[float, float, float]:
    #    thresh = sk.filters.threshold_otsu(im) This wasn't always working well
    thresh = skfilters.threshold_li(im)
    binar = im > thresh
    regions = sk.measure.regionprops(binar.astype(np.uint8))
    bubble = regions[0]  # this will be the largest detected region.
    y0, x0 = bubble.centroid
    r0 = bubble.major_axis_length / 2  # These are our initial values that we will start our optimization with.

    def cost(args: (float, float,
                    float)):  # We have to use args here rather than individual arguments because of out the sp.optimize function works. the binarized image is included in the function using closure.
        """Calculate the cost to be minimized which in this case is the negative of the number of pixels that overlap between our circle(x,y,r) and the binary image."""
        x, y, r = args
        coords = sk.draw.circle(y, x, r, shape=binar.shape)
        template = np.zeros_like(binar)
        template[coords] = True
        return -(np.sum(template == binar))

    for meth in ['Nelder-Mead',
                'Powell',
                'CG',
                'BFGS',
                'Newton-CG',
                'L-BFGS-B',
                'TNC',
                'COBYLA',
                'SLSQP',
                'dogleg' 
                'trust-ncg']:
        t = time.time()
        try:
            sp.optimize.minimize(cost, x0=(x0, y0, r0), method=meth, jac=False)
        except:
            print("Error")
        print(meth, time.time()-t)

    t = time.time()
    X, Y, R = sp.optimize.fmin(cost, (x0, y0, r0))
    print(time.time()-t)
    t = time.time()
    return X, Y, R