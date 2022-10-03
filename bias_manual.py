#!/usr/bin/python

# LSST FITS Header Conformance Tools
# Opens a file (or set of files) written by UCDavis
# Optical Simulator and modifes the 
# header to conform to LSST EO Test data standards
# Craig Lage 8-Jan-15 copied from Peter Doherty at Harvard
# and modified.

import pyfits as pf
import numpy as np
import sys
import subprocess
import warnings
import bias


###########################################################################
###########################################################################


infile = sys.argv[1]
biasfile = sys.argv[2]
newfile = infile.split('.fits')[0]+'_bias.fits'
bias.bias(infile, biasfile, newfile)
