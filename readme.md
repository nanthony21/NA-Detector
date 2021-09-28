## Overview
This UI streams images from a Thorlabs CCD camera connected to a microscope with a Bertrand lens in order to provide detailed microscope aperture alignment.
Aperture diameter can be automatically measured using a variety of methods. By measuring a reference NA (Objective collection numerical aperture), a target NA can be set. The UI will
then guide the user towards aligning the aperture with the target NA.

## Installation
This Python package is not currently automatically uploaded online to Pypi or Conda. It has been uploaded manually to the `backmanlab` anaconda cloud channel so it can be installed via Conda with `conda install -c backmanlab na-detector`. To install from source please download the source code and then install using `pip install .` or `python install setup.py`
