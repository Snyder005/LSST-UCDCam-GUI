#!/usr/bin/env python
# Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
# Date: 11-Oct-17
# This gest the exterior particle counts and saves them to a file

import numpy, time, datetime, sys, os, serial, struct, subprocess, urllib2
from pylab import *
#sys.path.append('/sandbox/lsst/lsst/GUI')

#************************************* SUBROUTINES ***********************************************

def GetExteriorCounts():
    try:
        response = urllib2.urlopen('https://www.arb.ca.gov')
        response.close()
        response = urllib2.urlopen('https://www.arb.ca.gov/aqmis2/display.php?download=y&param=PM25HR&units=001&year=2017&report=SITE1YR&statistic=DAVG&site=2143&ptype=aqd&monitor=-&std15= ')
        time.sleep(1.0)
        data = response.read()
        response.close()
    except Exception as e:
        print "Failed to read Exterior particle counts. Exception of type %s and args = \n"%type(e).__name__, e.args    
        sys.stdout.flush()
        return 0
    lines = data.split('\r\n')
    test = list(lines[0].split()[0])[0]
    if test == "s":
        file = open("exterior_counts.txt","w")
        file.write(data)
        file.close()
        return 1
    else:
        return 0

#************************************* MAIN PROGRAM ***********************************************
print "Starting. Current time = ", datetime.datetime.now()
success = GetExteriorCounts()
if success == 1:
    print "Got the data!"
else:
    print "Failed!"
#************************************* END MAIN PROGRAM ***********************************************
