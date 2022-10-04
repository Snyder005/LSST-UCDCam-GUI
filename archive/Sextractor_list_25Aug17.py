import matplotlib
matplotlib.use("PDF")
import pyfits,glob,time,scipy
import scipy.interpolate
from scipy.special import erf
from scipy.ndimage import shift
from pylab import *
from subprocess import call
from scipy.optimize import fmin_powell


#****************SUBROUTINES*****************
topdir = "/sandbox/lsst/lsst/GUI/"
configfile=topdir+'sextractor/default-array_dither.sex'
paramfile=topdir+'sextractor/default-array_dither.param'
maskdir=topdir+'sextractor/masks/'

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
    

#****************MAIN PROGRAM*****************
datadir=topdir+'20170831_002_spots'

zfilelist = []
for i in range(3,5):
    zfilelist=zfilelist+list(sort(glob.glob(datadir+'/ITL-3800C-002_spot_spot_%d??_20170831??????.fits'%i)))

print len(zfilelist)
sys.stdout.flush()


for fitsfilename in zfilelist: 
    tfile1=time.time() 
    for i in [1,8,12,13]:
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
