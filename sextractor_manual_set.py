import matplotlib
matplotlib.use("Agg")
import pyfits,sys,glob,time,scipy
import scipy.interpolate
from scipy.special import erf
from pylab import *
from subprocess import call
from IPython import parallel
from scipy.optimize import fmin_powell
#sys.path.append('/sandbox/lsst/lsst/GUI/notebooks')

topdir='/sandbox/lsst/lsst/GUI/'
thedir=topdir+'notebooks/'
datadir=topdir+'testdata/'

configfile=topdir+'sextractor/default-array_dither.sex'
paramfile=topdir+'sextractor/default-array_dither.param'
maskdir=topdir+'sextractor/masks/'


####### SUBROUTINES ##########

def remove_overscan_xy(image,x_overscan_start,x_overscan_end,y_overscan_start,y_overscan_end):
    overscan=image[:y_overscan_start,x_overscan_start+1:x_overscan_end]
    image=image[:y_overscan_start,:x_overscan_start]
    finalimg=image-matrix(median(overscan,axis=1)).T*np.ones(shape(image)[1])
    return array(finalimg)

def make_reg_from_ldac(cat_ldac_file,text_tag):
    thecat=pyfits.getdata(cat_ldac_file,'LDAC_OBJECTS')
    f = open(cat_ldac_file+'.reg','w')
    for i in range(len(thecat)):
        xcoo,ycoo=thecat['XWIN_IMAGE'][i],thecat['YWIN_IMAGE'][i]
        r=thecat['A_IMAGE'][i]
        thetext=thecat[text_tag][i]
        f.write('circle '+str(xcoo)+' '+str(ycoo)+' '+str(r)+'#text="'+str(thetext)+'"\n')
    f.close()
    
def Area(xl, xh, yl, yh, sigmax, sigmay, Imax):
    # Calculates how much of a 2D Gaussian falls within a rectangular box
    ssigx = sqrt(2) * sigmax
    ssigy = sqrt(2) * sigmay    
    I = (erf(xh/ssigx)-erf(xl/ssigx))*(erf(yh/ssigy)-erf(yl/ssigy))
    return Imax * I / 4.0

# This definition runs sextractor in parallel and can be given to IPython's parallel map function along with
#   the file list
def ovsub_runsex_makereg(fitsfilename):
    import pyfits
    import numpy as np
    from subprocess import call
    topdir='/Users/cslage/Research/LSST/code/GUI/'
    thedir=topdir+'profiles'

    configfile=topdir+'sextractor/default-array_dither.sex'
    paramfile=topdir+'sextractor/default-array_dither.param'
    maskdir=topdir+'sextractor/masks/'

    def remove_overscan_xy(image,x_overscan_start,x_overscan_end,y_overscan_start,y_overscan_end):
        overscan=image[:y_overscan_start,x_overscan_start+1:x_overscan_end]
        image=image[:y_overscan_start,:x_overscan_start]
        finalimg=image-np.matrix(np.median(overscan,axis=1)).T*np.ones(np.shape(image)[1])
        return finalimg

    def make_reg_from_ldac(cat_ldac_file,text_tag):
        thecat=pyfits.getdata(cat_ldac_file,'LDAC_OBJECTS')
        f = open(cat_ldac_file+'.reg','w')
        for i in range(len(thecat)):
            xcoo,ycoo=thecat['XWIN_IMAGE'][i],thecat['YWIN_IMAGE'][i]
            r=thecat['A_IMAGE'][i]
            thetext=thecat[text_tag][i]
            f.write('circle '+str(xcoo)+' '+str(ycoo)+' '+str(r)+'#text="'+str(thetext)+'"\n')
        f.close()
    for i in range(1,17):
        extname=pyfits.getheader(fitsfilename,i)['EXTNAME']
        img=pyfits.getdata(fitsfilename,extname)
        overscansubimg=remove_overscan_xy(img,509,542,2000,2022)   # cut off the overscan
        outname=fitsfilename[:-5]+extname+'.fits'
        pyfits.writeto(outname,overscansubimg,clobber=True)
        test=call(["sex",outname,"-c",configfile,"-CATALOG_NAME",outname+'.cat'])
        make_reg_from_ldac(outname+'.cat','NUMBER')


########MAIN PROGRAM#########



zfilelist=sort(glob.glob(sys.argv[1]))
print "Running %d files"%len(zfilelist)

for fitsfilename in zfilelist: 
    tfile1=time.time() 
    for i in [4,5,12,13]:
        tstart=time.time() 
        extname=pyfits.getheader(fitsfilename,i)['EXTNAME'] 
        img=pyfits.getdata(fitsfilename,extname) 
        overscansubimg=remove_overscan_xy(img,509,542,2000,2022) 
        # cut off the overscan 
        outname=fitsfilename[:-5]+extname+'.fits' 
        pyfits.writeto(outname,overscansubimg,clobber=True) 
        test=call(["sex",outname,"-c",configfile,"-CATALOG_NAME",outname+'.cat']) 
        make_reg_from_ldac(outname+'.cat','NUMBER') 
        tend=time.time() 
        print extname+" time: "+str(tend-tstart)[:4] 
        print "Time taken for file "+str(fitsfilename[-26:-23])+": "+str(time.time()-tfile1)

