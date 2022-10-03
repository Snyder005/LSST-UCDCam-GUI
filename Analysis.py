#!/usr/bin/env python
#Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
#Date: 7-Jan-15
# These files contains various subroutines
# needed to run the LSST Simulator
# This class sets the Tkinter frame for the basic image analysis that is needed.
# Only basic operations included at the moment

# Using the Tkinter module for interface design, and matplotlib for plotting
from Tkinter import *
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

#other packages necessary for communication and analysis
import numpy, time, sys, fcntl, serial, socket, struct
import os, signal,subprocess
import pyfits
#ds9 for display
from ds9 import *
import overscan_subtract
import overscan_crosstalk

class Analysis(object):
    def __init__(self, master, camera):
        self.master = master
        self.sexpath='sex'
        self.sexconfigfile='/sandbox/lsst/lsst/GUI/sextractor/pinhole.sex'
        self.sexparamfile='/sandbox/lsst/lsst/GUI/sextractor/pinhole.param'
        self.camera = camera
        return

    def Plot_Histogram(self):
        """ A demonstration function, which takes in the filename, opens with pyfits, and plots a histogram
	to the analysis frame using FigureCanvasTkAgg"""
        print "Plotting Pixel Histogram"
        f = Figure(figsize=(7,7), dpi=72)
        ax = f.add_subplot(111)
        try:
            file = pyfits.open(self.camera.fitsfilename)
        except (IOError, NameError, TypeError, ValueError) as e:
            print "Failure in fits open. Exception of type %s and args = \n"%type(e).__name__, e.args    
            print "No fits file specified.  Opening test file\n"
            file = pyfits.open("testdata/40kpinholearray.fits")

        try:
            segment = int(self.hist_segment.get())
        except (IOError, NameError, TypeError, ValueError) as e:
            print "Failure in segemnt histogram. Exception of type %s and args = \n"%type(e).__name__, e.args    
            print "No segment entered. Plotting segment 1. \n"
            segment = 1
        data = file[segment].data 
        data = data.flatten()
        med = numpy.median(data)
        mean = numpy.average(data)
        std = numpy.std(data)
        minval = data.min()
        maxval = data.max()
        #minval = 0.95 * med
        maxval = mean + 6.0 * std
        print minval,maxval,med,std
        data = data[data>minval]
        data = data[data<maxval]
        ax.set_title("Pixel Histogram - %s, Segment %d"%(self.camera.fitsfilename, segment))
        ax.set_xlabel("Pixel Value")
        f.text(0.4,0.8,"Min = %.1f, Max = %.1f"%(minval, maxval))
        ax.hist(data, 100, histtype = 'stepfilled', log=True)
        dataPlot = FigureCanvasTkAgg(f, self.frame)
        dataPlot.show()
        dataPlot.get_tk_widget().grid(row=4, column=0,columnspan=5,rowspan=3)
        return

    def run_sextractor(self):
	""" Runs sextractor on a given frame, using the parameters given in the Define_Frame definition below. Also reads in the
	sextractor catalogs created, and makes a region file of the X/Y coordinates which can then be sent to DS9"""
        fall=open(self.camera.fitsfilename+'all.cat.reg','w')   # this is the region file containing all of the objects
        fall.write("# Region file format: DS9 version 4.1\n")   # necessary DS9 region file header
        fall.write("global color=green dashlist=8 3 width=1 select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1\nimage\n")
	for extnum in numpy.arange(1,17):
            self.fitsext=pyfits.getdata(self.camera.fitsfilename,extnum)    # grab one segment of the CCD at a time
            hdrext=pyfits.getheader(self.camera.fitsfilename,extnum)
	    extname=hdrext['EXTNAME']
            # get overscan size info from the header!!
  		# CHANGE LATER? JUST SHORTCUT TO THE KNOWN OVERSCAN REGION, NO HDR INFO
	    overscan_start,overscan_end=509,542#xsize-overscan_xsize,xsize
	    maskimagename='/sandbox/lsst/lsst/GUI/sextractor/masks/mask_'+extname+'.fits'
    	    overscan=self.fitsext[:2000,overscan_start+1:overscan_end]
       	    image=self.fitsext[:2000,0:overscan_start]
	    # median of the ovescan row is now subtracted from the frame
       	    finalimg=image-numpy.matrix(numpy.median(overscan,axis=1)).T*numpy.ones(numpy.shape(image)[1])  
            self.fitsext=finalimg
            self.outname=self.camera.fitsfilename[:-5]+'seg'+str(extnum)+'.fits'
	    print self.outname
            pyfits.writeto(self.outname,self.fitsext,clobber=True)
    	    print "Running sextractor on "+self.camera.fitsfilename+", segment "+str(extnum)
	    # now run sextractor using the parameters defined by the user input
    	    test=subprocess.call([self.sexpath,self.outname,"-c",self.sexconfigfile,"-PARAMETERS_NAME",self.sexparamfile,
		"-DETECT_MINAREA",self.sex_minpix.get(),"-DETECT_THRESH",self.sex_minsig.get(),
		"-WEIGHT_IMAGE",maskimagename,"-WEIGHT_TYPE","MAP_WEIGHT",
		"-ANALYSIS_THRESH",self.sex_minsig.get(),"-CATALOG_NAME",self.outname+'.cat'])#,"-VERBOSE_TYPE","QUIET"])
    	    #now make a region file for the catalog. first read it in
	    self.thecat=pyfits.getdata(self.outname+'.cat','LDAC_OBJECTS')
    	    f = open(self.outname+'.cat.reg','w')
	    fall.write("# tile "+str(extnum)+"\n")    # DS9 needs this for each segment's regions when in mosaic mode
    	    for i in range(len(self.thecat)):
    	        xcoo,ycoo=self.thecat['XWIN_IMAGE'][i],self.thecat['YWIN_IMAGE'][i]
    	        r=self.thecat['A_IMAGE'][i]
    	        thetext=self.thecat["MAG_AUTO"][i]
		# using the region file syntax, output the XY coordinates and a text tag to the region file
    	        f.write('circle '+str(xcoo)+' '+str(ycoo)+' '+str(r)+'#text="'+str(thetext)+'"\n')    #individual segment
    	        fall.write('circle '+str(xcoo)+' '+str(ycoo)+' '+str(r)+'#text="'+str(thetext)+'"\n') #all segments
            f.close()
    	call(['rm',outname])
        fall.close()
	return

    def open_ds9(self):
	"""Opens DS9 using pyds9, sending an arbitrary test image at this point"""
	self.d=ds9()
        try:
            self.d.set('file mosaicimage iraf '+self.camera.fitsfilename)   # the proper XPA syntax for opening a mosaic image in DS9
        except Exception as e:
            print "Fits file entry error. Exception of type %s and args = \n"%type(e).__name__, e.args    
            print "No fits file specified.  Opening test file\n"
            self.d.set('file mosaicimage iraf testdata/40kpinholearray.fits')   # the proper XPA syntax for opening a mosaic image in DS9
	return

    def send_ds9_regionfiles(self):
	""" Sends the open session of DS9 a region file to open, using the XPA messaging syntax"""
	self.d.set('regions delete all')
	self.d.set('regions load '+self.camera.fitsfilename+'all.cat.reg')


    def Define_Frame(self):
        """This defines the buttons and layout for the Analysis frame"""
        self.frame=Frame(self.master, relief=GROOVE, bd=4)
        self.frame.grid(row=4,column=4,rowspan=4,columnspan=2)
        frame_title = Label(self.frame,text="Data Analysis",relief=RAISED,bd=2,width=12, bg="light yellow",font=("Times", 16))
        frame_title.grid(row=0, column=1)

        ovscan_but = Button(self.frame, text="Perform Overscan Subtraction", width=24,command=self.overscan_subtraction)
        ovscan_but.grid(row=0,column=0)
        crosstalk_but = Button(self.frame, text="Perform Overscan and Crosstalk Subtraction", width=36, command=self.crosstalk_subtraction)
        crosstalk_but.grid(row=3,column=0)

        ds9_but = Button(self.frame, text="Show frame", width=12,command=self.open_ds9)
        ds9_but.grid(row=3,column=1)

        histogram_but = Button(self.frame, text="Plot Histogram Segment:", width=20, command=self.Plot_Histogram)
        histogram_but.grid(row=1,column=1)
        self.hist_segment = Entry(self.frame, justify="center", width=12)
        self.hist_segment.grid(row=1, column=2)

        self.sex_minpix = Entry(self.frame, justify="center", width=12)
        self.sex_minpix.grid(row=4,column=0)
	sex_minpix_label= Label(self.frame,text="Min # of pix for detect", width=20,font=("Times", 10))
	sex_minpix_label.grid(row=5,column=0)
        self.sex_minsig = Entry(self.frame, justify="center", width=12)
        self.sex_minsig.grid(row=6,column=0)
	sex_minsig_label= Label(self.frame,text="Min # sig for detect", width=20,font=("Times", 10))
	sex_minsig_label.grid(row=7,column=0)
	sextractor_but = Button(self.frame, text="Run sextractor", width=12,command=self.run_sextractor)
        sextractor_but.grid(row=8,column=0)
        ds9_reg_but = Button(self.frame, text="Show regions", width=12,command=self.send_ds9_regionfiles)
        ds9_reg_but.grid(row=4,column=1)
        return

    def overscan_subtraction(self):
	""" Runs overscan subtraction on the latest file and creates a new fits file"""
        infile = self.camera.fitsfilename
        newfile = infile.split('.fits')[0]+'_ov.fits'
        self.camera.fitsfilename = newfile
        overscan_subtract.overscan_subtract(infile, newfile)
        print "Overscan subtracted file = %s\n"%self.camera.fitsfilename
        return

    def crosstalk_subtraction(self):
	""" Runs overscan subtraction and crosstalk subtraction on the latest file and creates a new fits file"""
        infile = self.camera.fitsfilename
        newfile = infile.split('.fits')[0]+'_ov_ct.fits'
        self.camera.fitsfilename = newfile
        overscan_crosstalk.overscan_crosstalk_subtract(infile,  newfile)
        print "Crosstalk and overscan subtracted file = %s\n"%self.camera.fitsfilename
        return
