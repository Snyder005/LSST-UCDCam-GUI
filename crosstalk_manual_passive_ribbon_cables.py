#!/usr/bin/python

# LSST FITS Header Conformance Tools
# Opens a file (or set of files) written by UCDavis
# Optical Simulator and modifes the 
# header to conform to LSST EO Test data standards
# Craig Lage 8-Jan-15 copied from Peter Doherty at Harvard
# and modified.
# Added crosstalk subtraction 21-Aug-15 Craig Lage


from pylab import *
import pyfits as pf
import sys
import subprocess
import warnings


###########################################################################
###########################################################################
# This ignores an annoying deprecation warning.  Will fix later.
#warnings.simplefilter("ignore")

def crosstalk_subtract(infile, newfile):

    print 'Performing crosstalk subtraction on FITS file :', infile
    # The crosstalk matrix below was calculated from spot images on 8-Jan-16
    
    ct_matrix = zeros([16,16])
    ct_matrix = array([
[ 1.0000, 0.0129, 0.0035, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0428],
[ 0.0132, 1.0000, 0.0134, 0.0025, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
[ 0.0034, 0.0108, 1.0000, 0.0116, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
[ 0.0000, 0.0022, 0.0115, 1.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
[ 0.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0147, 0.0021, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
[ 0.0000, 0.0000, 0.0000, 0.0000, 0.0151, 1.0000, 0.0118, 0.0038, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
[ 0.0000, 0.0000, 0.0000, 0.0000, 0.0021, 0.0110, 1.0000, 0.0125, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
[ 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0035, 0.0119, 1.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
[ 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0113, 0.0030, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000],
[ 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0114, 1.0000, 0.0096, 0.0018, 0.0000, 0.0000, 0.0000, 0.0000],
[ 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0034, 0.0105, 1.0000, 0.0106, 0.0000, 0.0000, 0.0000, 0.0000],
[ 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0028, 0.0110, 1.0000, 0.0000, 0.0000, 0.0000, 0.0000],
[ 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0104, 0.0017, 0.0000],
[ 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0103, 1.0000, 0.0097, 0.0134],
[ 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0019, 0.0125, 1.0000, 0.0543],
[ 0.0015, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0008, 0.0034, 1.0000]])



    # copy the file
    command = 'cp '+infile+' '+newfile
    copyfile = subprocess.Popen(command, shell=True)
    subprocess.Popen.wait(copyfile)

    # open the file
    # do_not_scale_image_data=True is important so as not to mess up the data format.
    # checksum=True is required to calculate the checksums and datasums
    hdulist = pf.open(newfile, mode='update', do_not_scale_image_data=True)
    
    ###########################################################################
    # fix up the various image extensions
    
    # First the overscan subtraction.
    ov_data = []
    for i in range(1,17) :
        data = np.array(hdulist[i].data + 32768, dtype = np.int32)
        overscan = data[2005:2021,:].sum(axis=0) / 16.0
        ov_data.append(np.clip((data-overscan), 0, 65536))

    # Next the crosstalk subtraction.
    newdata = []
    for i in range(1,17) :
        data = np.array(hdulist[i].data + 32768, dtype = np.int32)
        for j in range(1,17):
            if i == j or ct_matrix[i-1,j-1] < 1.0E-9:
                continue
            data = data - ct_matrix[i-1,j-1] * ov_data[j-1]
        newdata.append(np.clip(data, 0, 65536))
    for i in range(1,17) :
        hdulist[i].data = np.array(newdata[i-1] - 32768, dtype=np.int16)
        # Data is stored as unsigned 16 bit integers, so we need to apply this transformation
        # in order to calculate the mean and std deviation.
    
    # finished. Close file.
    hdulist.close(output_verify='ignore')

    print 'FITS file conversion done.'

    return

##########################################################################

infile = sys.argv[1]
newfile = infile.split('.fits')[0]+'_ct.fits'
crosstalk_subtract(infile, newfile)
