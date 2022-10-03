import matplotlib
matplotlib.use("Agg")
import pyfits,sys,glob,time,scipy
import scipy.interpolate
from scipy.special import erf
from pylab import *
from subprocess import call
from IPython import parallel
from scipy.optimize import fmin_powell
sys.path.append('/sandbox/lsst/lsst/GUI/notebooks')
topdir='/sandbox/lsst/lsst/GUI/'
thedir=topdir+'notebooks/'
datadir=topdir+'testdata/'

configfile=topdir+'sextractor/default-array_dither.sex'
paramfile=topdir+'sextractor/default-array_dither.param'
maskdir=topdir+'sextractor/masks/'

####SUBROUTINES######

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


class Array2dSet:
    def __init__(self,xmin,xmax,nx,ymin,ymax,ny,nstamps):
        # This packages up a set of nstamps postage stamp images,
        # each image of which is nx * ny pixels
        self.nx=nx
        self.ny=ny
        self.nstamps=nstamps

        self.xmin=xmin
        self.ymin=ymin
        
        self.xmax=xmax
        self.ymax=ymax
        
        self.dx=(xmax-xmin)/nx
        self.dy=(ymax-ymin)/ny
        
        self.x=linspace(xmin+self.dx/2,xmax-self.dx/2,nx)
        self.y=linspace(ymin+self.dy/2,ymax-self.dy/2,ny)

        self.data=zeros([nx,ny,nstamps])
        self.xoffset=zeros([nstamps])
        self.yoffset=zeros([nstamps])
        self.imax=zeros([nstamps])


def BuildSpotList(fitsfilename, segmentnumber, numspots, nx, ny, minsize, maxsize):
    stampxmin = -(int(nx/2)+0.5)
    stampxmax = -stampxmin
    stampymin = -(int(ny/2)+0.5)
    stampymax = -stampymin
    xcoomin = 50
    xcoomax = 450
    ycoomin = 1400
    ycoomax = 1900
    spotlist = Array2dSet(stampxmin,stampxmax,nx,stampymin,stampymax,ny,numspots)
    hdr=pyfits.getheader(fitsfilename,segmentnumber)
    extname = hdr['EXTNAME']
    img=pyfits.getdata(fitsfilename,extname) 
    overscansubimg=remove_overscan_xy(img,509,542,2000,2022) 
    catname=fitsfilename[:-5]+extname+'.fits.cat.reg' 
    catfile = open(catname,'r')
    catlines = catfile.readlines()
    catfile.close()
    n=0
    for line in catlines:
        try:
            size = float(line.split()[3].split('#')[0])
            if size < minsize or size > maxsize:
                continue
            xcoord = float(line.split()[1])
            ycoord = float(line.split()[2])
            if xcoord < xcoomin or xcoord > xcoomax or ycoord < ycoomin or ycoord > ycoomax:
                continue
            xint = int(xcoord-0.5)
            yint = int(ycoord-0.5)
            xmin = xint - int(nx/2)
            xmax = xint + int(nx/2) + 1
            ymin = yint - int(ny/2)
            ymax = yint + int(ny/2) + 1
            stamp = overscansubimg[ymin:ymax, xmin:xmax]
           
            xsum = 0.0
            ysum = 0.0
            datasum = 0.0
             
            for i in range(nx):
                for j in range(ny):
                    spotlist.data[i,j,n] = float(stamp[j,i])                    
                    ysum += spotlist.y[j] * spotlist.data[i,j,n]
                    xsum += spotlist.x[i] * spotlist.data[i,j,n]
                    datasum += spotlist.data[i,j,n]
            xoff = xsum / datasum
            yoff = ysum / datasum
            spotlist.xoffset[n] = xoff#xcoord - xint - 1.0
            spotlist.yoffset[n] = yoff#ycoord - yint - 1.0     
                    
            n += 1
            if n == numspots:
                return spotlist
        except:
            continue
    # Reaching this point means we found less spots than requested.
    newspotlist = Array2dSet(stampxmin,stampxmax,nx,stampymin,stampymax,ny,n)
    newspotlist.xoffset = spotlist.xoffset[0:n]
    newspotlist.yoffset = spotlist.yoffset[0:n]
    newspotlist.data = spotlist.data[:,:,0:n]
    del spotlist
    return newspotlist

import forward

def FOM(params):
    [sigmax, sigmay] = params
    result = forward.forward(spotlist,sigmax,sigmay)
    return result

def PyFOM(params):
    fom = 0.0
    [Imax, sigmax, sigmay] = params
    area=zeros([spotlist.nx,spotlist.ny])
   
    for spot in range(spotlist.nstamps):
        for ii in range(spotlist.nx):
            for jj in range(spotlist.ny):
                xl = spotlist.x[ii] - spotlist.xoffset[spot] - 0.5
                xh = xl + 1.0
                yl = spotlist.y[jj] - spotlist.yoffset[spot] - 0.5
                yh = yl + 1.0
                #if spot == 78 and ii == 4 and jj == 4 or spot==0:
                    #print "ii = %d, jj = %d, img = %.4f"%(ii,jj,spotlist.data[ii,jj,spot])
                #print "ii = %d, jj = %d,xl = %.2f, xh = %.2f, yl = %.2f, yh = %.2f"%(ii,jj,xl,xh,yl,yh)
                area[ii,jj] = Area(xl, xh, yl, yh, sigmax, sigmay, Imax)
                fom += square(area[ii,jj]-spotlist.data[ii,jj,spot])
    #print "Imax = %.1f, sigmax = %.2f, sigmay = %.2f, fom = %.1f"%(Imax, sigmax, sigmay, fom)
    return fom

######MAIN PROGRAM#########

zfilelist=sort(glob.glob(sys.argv[1]))
print "Processing %d files"%len(zfilelist)
firstnum = zfilelist[0].split('_')[3].strip('??')

import gc
nx = 9
ny = 9
numspots = 400
numfiles = len(zfilelist)
sigmaxs = zeros([1,numfiles])
sigmays = zeros([1,numfiles])
imaxs = zeros([1,numfiles])
totelectrons = zeros([1,numfiles])
gains = [5.20,5.29,5.26,5.32]

for i, segmentnumber in enumerate([4]):#,5,12,13]):
    gain = gains[i]

    for j,fitsfilename in enumerate(zfilelist):
        param0 = [1.0, 1.0]
    
        spotlist = BuildSpotList(fitsfilename, segmentnumber, numspots, nx, ny,0.7,1.4)
        print "nstamps = %d"%spotlist.nstamps
        args = ()#(spotlist)
        Result = fmin_powell(FOM, param0, args)

        print fitsfilename
        imax = spotlist.imax.mean()
        ADU_correction = Area(-0.5,0.5,-0.5,0.5,Result[0],Result[1],1.0)
        tote = spotlist.data.sum() * gain / spotlist.nstamps # Total electrons in the stamp
        print Result, imax, tote
        imaxs[i,j] = imax * ADU_correction * gain
        sigmaxs[i,j] = Result[0]
        sigmays[i,j] = Result[1]
        totelectrons[i,j] = tote
        del spotlist
        gc.collect()

from scipy import stats
rcParams.update({'font.size':18})
mask = []#[19, 20, 22]#[15,19,22,23,24,25,26,28,29,30,31]#[18,19,21,22,24,25]# # Bad values ???

for i, segmentnumber in enumerate([4]):#,5,12,13]):
    hdr=pyfits.getheader(zfilelist[0],segmentnumber)
    extname = hdr['EXTNAME']

    figure()
    title("Brighter-Fatter - 30 micron Spots - %s"%extname)
    #title("Brighter-Fatter - 30 micron Spots")
    scatter(delete(imaxs[i,:],mask), delete(sigmaxs[i,:],mask), color = 'green', lw = 2, label = 'Sigma-x')
    scatter(delete(imaxs[i,:],mask), delete(sigmays[i,:],mask), color = 'red', lw = 2, label = 'Sigma-y')

    slope, intercept, r_value, p_value, std_err = stats.linregress(imaxs[i,4:8],sigmaxs[i,4:8])

    xplot=linspace(-5000.0,200000.0,100)
    yplot = slope * xplot + intercept
    plot(xplot, yplot, color='blue', lw = 2, ls = '--')
    tslope = slope * 100.0 * 50000.0
    #text(10000.0,1.03,"X Slope = %.2f %% per 50K e-, Intercept = %.3f"%(tslope,intercept))
    text(2000.0,1.08,"X Slope = %.2f %% per 50K e-"%tslope, fontsize = 24)

    slope, intercept, r_value, p_value, std_err = stats.linregress(imaxs[i,4:8],sigmays[i,4:8])

    xplot=linspace(-5000.0,200000.0,100)
    yplot = slope * xplot + intercept
    plot(xplot, yplot, color='black', lw = 2, ls = '--')
    tslope = slope * 100.0 * 50000.0
    #text(10000.0,1.02,"Y Slope = %.2f %% per 50K e-, Intercept = %.3f"%(tslope,intercept))
    text(2000.0,1.06,"Y Slope = %.2f %% per 50K e-"%tslope, fontsize = 24)

    xlim(0.0,400000.0)
    xticks([0.0,100000,200000,300000])
    ylim(0.90,1.10)
    xlabel('Central Peak(electrons)')
    ylabel('Sigma (Pixels)')
    legend(loc= 'lower right')
    savefig(datadir+"Forward_Model_Spots_Test_%s_%s.png"%(firstnum,extname))
"""
segmentnumber = 4
hdr=pyfits.getheader(zfilelist[0],segmentnumber)
extname = hdr['EXTNAME']
gain = gains[0]

figure()
testn = 5
spot = 327
numspots = 400
fitsfilename = zfilelist[testn]
spotlist = BuildSpotList(fitsfilename, segmentnumber, numspots, nx, ny,0.7,3.0)
param0 = [1.0, 1.0]
args = ()#(spotlist)
Result = fmin_powell(FOM, param0, args)
sigmax = Result[0]
sigmay = Result[1]
ADU_correction = Area(-0.5,0.5,-0.5,0.5,sigmax, sigmay,1.0)
Imax = spotlist.imax[spot] 
seqno = int(zfilelist[testn].split("_")[4])
suptitle=("Sequence # %d, Spot # %d"%(seqno,spot))
area=zeros([nx,ny])
for ii in range(nx):
    for jj in range(ny):
        xl = ii - int(nx/2) - spotlist.xoffset[spot] - 0.5
        xh = xl + 1.0
        yl = jj - int(ny/2) - spotlist.yoffset[spot] - 0.5
        yh = yl + 1.0
        area[ii,jj] = Area(xl, xh, yl, yh, sigmax, sigmay, Imax) 


subplots_adjust(wspace = 2.0)
subplot(1,3,1)
imshow(spotlist.data[:,:,spot] ,interpolation="None")
subplot(1,3,2)
plot(spotlist.data[int(nx/2),:,spot] , lw = 2, label="Data")
plot(area[int(nx/2),:], lw = 2, label="Model")
xlabel("X (Pixels)")
ylabel("Signal(ADU)")
xticks([0,2,4,6,8])
subplot(1,3,3)
plot(spotlist.data[:,int(ny/2),spot], lw = 2, label="Data")
plot(area[:,int(ny/2)], lw = 2, label="Model")
xlabel("Y (Pixels)")
ylabel("Signal(ADU)")
xticks([0,2,4,6,8])
legend(loc = (-6.5,0.8))
savefig(datadir+"Typical_Fit_%s_%s_%s"%(firstnum,testn,extname))

mask = []#[15,19,22,23,24,25,26,28,29,30,31]#[19,20,22]
from scipy import stats
figure()
exp_current=[]
masked_zfilelist = delete(zfilelist,mask)
for i,fitsfilename in enumerate(masked_zfilelist):
    try:
        exptime=pyfits.getheader(fitsfilename,0)['EXPTIME'] 
        mondiode=pyfits.getheader(fitsfilename,0)['MONDIODE'] 
        exp_current.append(float(exptime) * mondiode / (1.0E-9))
    except:
        continue
slope, intercept, r_value, p_value, std_err = stats.linregress(exp_current[0:10],imaxs[0,0:10])

xplot=linspace(0.0,7.0,100)
yplot = slope * xplot + intercept
scatter(exp_current,delete(imaxs[0,:],mask)/1.0E3)
plot(xplot, yplot/1.0E3, color='red')
text(5.0,60,"Linear Fit R^2 = %.5f"%r_value)
xlabel("Exp Time * Monitor Diode (nA-sec)")
ylabel("Modeled Peak Intensity (10^3 e-)")
#xlim(0.0, 7.0)
#ylim(0.0,350.0)
savefig(datadir+"Intensity_Check_%s.png"%firstnum)
"""
