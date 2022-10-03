#! /usr/bin/env python 

# eolib.py
#
# functions that are used by the LSST ccdacq program and related codes
# Craig Lage - UCDavis 8-Jan-15 - Copied from Peter Doherty at Harvard


#import sys
import os
import time
import glob
    

###############################################################################
# ccdacqHelp : print useful (hopefuly) information for the user to peruse
def help():  
    print ' ' 
    print 'Usage: ccdacq <serno> <config_file> <test> [<test> <test> ..]'
    print 'where <test> may be any of: '
    print 'dark    : aquire a set of dark integrations'
    print 'flat    : acquire a set of flat field exposures'
    print 'lambda  : acquire a set of flat field exposures at various wavelengths'
    print 'wl      : same as lambda'
    print 'ppump   : acquire exposures with and without pocket pumping'
    print 'sflat   : acquire sets of identical flat field exposures'
    print 'fe55    : acquire one or more sets of Fe55 exposures'
    print 'fluxcal : recalibrate the flux computation system using existing file if present'
    print 'fluxnew : recalibrate the flux computation system and force new file creation'
    print 'cmd     : enter interactive command interpreter'
    print 'all     : perform all tests including flux calibration'
    print 'help    : print this information'
    print ' ' 
    return
  

                   
###############################################################################
# create a time stamp
def tstamp():
    tstamp=time.strftime("%Y%m%d%H%M%S")
    return tstamp
    
###############################################################################
# read in the eotest_acq.cfg file and get keyword value
# Find the first occurance and return string. Return default value if not found.
def getCfgVal(cfgfile, name, default="NOT FOUND"):
    value = default
    with open(cfgfile) as fp:
        for line in fp:
            tokens = str.split(line)
            if (len(tokens) >= 2): 
                if (tokens[0].upper() == name.upper() ):
                     value = tokens[1]
                     break
    return value

###############################################################################
# Read the flux vs wl calibration file and get flux associated with a wl
# Find the first occurance of the reuested wl and return value
def getFluxcalVal(calfile, wl):
    wl = float(wl)
    with open(calfile) as fp:
        for line in fp:
            tokens = str.split(line)
            if (len(tokens) > 0): 
                 if ((tokens[0] == 'fluxcal') and (float(tokens[1]) == wl)):
                     break
    return float(tokens[2])

###############################################################################
# Read the flux vs wl calibration file and get flux associated with a wl
# Find the first occurance of the reuested wl or the next higher and return 
# a value, either of the wavelength requested (if found) or interpolated.
def getFluxcalFlux(calfile, wl):
    wl = float(wl)
    wavelengths = []
    fluxes = []
    with open(calfile) as fp:
        for line in fp:
            tokens = str.split(line)
            if (len(tokens) > 0): 
                 if (tokens[0] == 'fluxcal'): 
                    wavelengths.append(float(tokens[1]))
		    fluxes.append(float(tokens[2]))
    waves = sorted(wavelengths)
    for i in range(len(wavelengths)):
        if (wavelengths[i] > wl):
	    break
    low = wavelengths[i-1]
    high = wavelengths[i]
    if (low == wl):  # we found an exact match
        return getFluxcalVal(calfile, wl)
    else:
        lowf = getFluxcalVal(calfile, low) 
        highf = getFluxcalVal(calfile, high) 
	flux = lowf - (((wl-low)/(high-low)) * (lowf - highf))
    return flux

###############################################################################
# expCalc: compute the exposure time required to reach a target signal level 
# at a specified wavelength
def expCalc(calfile, wl, target, nd=0.0):
    flux = getFluxcalFlux(calfile, wl) / pow(10,float(nd))
    exptime = float(target)/float(flux)
    return exptime

###############################################################################
# expCheck: check the exposure time required to reach a target signal level 
# at a specified wavelength is OK and optionally adjust ND filter.
def expCheck(lab, target, wl, hi_lim, lo_lim, test='TEST', use_nd=False):

    caldir  = getCfgVal(lab['config'],'BASE_DIR')+'/system/fluxcal'
    calfiles = sorted(glob.glob(caldir+'/fluxcal*.txt')) 
    calfile = calfiles[len(calfiles)-1]
    
    ndfilter = float(getCfgVal(lab['config'], 'ND_FILTER', default='2.0'))

    exptime = expCalc(calfile, wl, target)
    if (exptime < lo_lim):
        if (use_nd == True):
            lab['logger'].log("%s : Exposure time %6.2f is below lower limit." 
                               % (str.upper(test), exptime))
            lab['monochromator'].setFilter(5) # put the nd filter in place
            exptime = expCalc(calfile, wl, target, nd=ndfilter)
            lab['logger'].log("%s : Exp time with ND %4.2f Filter = %6.2f" 
                               % (str.upper(test), ndfilter, exptime))
        else:
            lab['logger'].log("%s : Exposure time limited to %6.2f sec." 
                               % (str.upper(test), lo_lim))
            exptime = lo_lim
    if (exptime > hi_lim):
        lab['logger'].log("%s : Exposure time limited to %6.2f sec." 
                           % (str.upper(test), hi_lim))
        exptime = hi_lim
    return exptime

###############################################################################
#def findCalfile(lab):
#    caldir  = getCfgVal(lab['config'],'BASE_DIR')+'/system/fluxcal'
#    calfiles = sorted(glob.glob(caldir+'/fluxcal*.txt')) 
#    calfile = calfiles[len(calfiles)-1]
#    return calfile
