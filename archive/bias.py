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


###########################################################################
###########################################################################
# This ignores an annoying deprecation warning.  Will fix later.
#warnings.simplefilter("ignore")

def bias(infile, biasfile, newfile):

    print 'Performing bias subtraction on FITS file :', infile

    # copy the file
    command = 'cp '+infile+' '+newfile
    copyfile = subprocess.Popen(command, shell=True)
    subprocess.Popen.wait(copyfile)

    # open the file
    # do_not_scale_image_data=True is important so as not to mess up the data format.
    # checksum=True is required to calculate the checksums and datasums
    hdulist = pf.open(newfile, mode='update', do_not_scale_image_data=True)
    biaslist = pf.open(biasfile, mode='readonly')
    ###########################################################################
    # fix up the various image extensions
    
    for i in range(1,17) :

        data = np.array(hdulist[i].data + 32768, dtype = np.int32)
        biasdata = np.array(biaslist[i].data, dtype = np.int32)
        data = np.clip(data-biasdata, 0, 65536)
        hdulist[i].data = np.array(data - 32768, dtype=np.int16)
        # Data is stored as unsigned 16 bit integers, so we need to apply this transformation
        # in order to calculate the mean and std deviation.

    # finished. Close file.
    hdulist.close(output_verify='ignore')

    print 'FITS file conversion done.'

    return
##########################################################################

