# -*- coding: utf-8 -*-
"""
Created on Thu May 30 09:56:28 2019

@author: backman05
"""
import time
from abc import ABC, abstractmethod

import skimage as sk
import skimage.filters as skfilters
from typing import Tuple, Callable
import numpy as np
import scipy as sp


def binarizeImageLi(im: np.ndarray) -> np.ndarray:
    """Take the Uint8 image from the camera and binarize it for further processing."""
    thresh = skfilters.threshold_li(im)
    binar = im > thresh
    return binar


def binarizeImageOtsu(im: np.ndarray) -> np.ndarray:
    """Take the Uint8 image from the camera and binarize it for further processing."""
    thresh = sk.filters.threshold_otsu(im)
    binar = im > thresh
    return binar


def initialGuessCircle(binary: np.ndarray):
    """Generate an initial guess for x, y, and r of the circle based on a binarized image."""
    regions = sk.measure.regionprops(binary.astype(np.uint8))
    try:
        bubble = regions[0]  # this will be the largest detected region.
        y0, x0 = bubble.centroid
        r0 = bubble.major_axis_length / 2  # These are our initial values that we will start our optimization with.
    except IndexError:  # In rare cases there is no region found
        x0, y0, r0 = 1, 1, 1
    return x0, y0, r0


def fitCircle(binar: np.ndarray, x0, y0, r0) -> Tuple[float, float, float]:
    def cost(args: (float, float, float)): #We have to use args here rather than individual arguments because of how the sp.optimize function works. the binarized image is included in the function using closure.
        """Calculate the cost to be minimized which in this case is the negative of the number of pixels that overlap between our circle(x,y,r) and the binary image."""
        x, y, r = args
        coords = sk.draw.circle(y, x, r, shape=binar.shape)
        template = np.zeros_like(binar) #Template is a binary array based on the x,y, and r
        template[coords] = True
        err = (np.sum(template == binar))
        # print(x, y, r)
        # print(err)
        return -(err) #The score is the number of pixels that are correct. should this be changed?
    
    result = sp.optimize.minimize(cost, x0=(x0, y0, r0), method='COBYLA', jac=None, options={'disp': False})
    X, Y, R = tuple(result.x)
    # print(result.success)
    # print(X,Y,R)
    return X, Y, R


def detectEdges(im: np.ndarray):
    from skimage.feature import canny
    #  detect edges
    edges = canny(im, sigma=3, low_threshold=10, high_threshold=50)
    return edges

def fitCircleHough(edges: np.ndarray, x0, y0, r0):
    """https://scikit-image.org/docs/dev/auto_examples/edges/plot_circular_elliptical_hough_transform.html"""
    from skimage.transform import hough_circle, hough_circle_peaks

    # Detect two radii
    hough_radii = np.arange(int(r0*.7), int(r0*1.1), 1)# We expect that the actual radius we be within range of the initial guess
    hough_res = hough_circle(edges, hough_radii)

    # Select the most prominent 3 circle
    accums, cx, cy, radii = hough_circle_peaks(hough_res, hough_radii, total_num_peaks=1)
    if len(cx) > 0:
        return cx[0], cy[0], radii[0]
    else:  # No circles were found
        return 0, 0, 0

def fitCircleTest(im: np.ndarray) -> Tuple[float, float, float]:
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