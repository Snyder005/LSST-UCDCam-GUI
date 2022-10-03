#!/usr/bin/env python
# Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
# Date: 11-Oct-17
# This gest the exterior particle counts and saves them to a file

import time, sys
from pylab import *
from selenium import webdriver

#************************************* SUBROUTINES ***********************************************

def GetExteriorCounts():
    driver = webdriver.Firefox()
    driver.get('https://www.arb.ca.gov/aqmis2/display.php?download=y&param=PM25HR&units=001&year=2017&report=SITE1YR&statistic=DAVG&site=2143&ptype=aqd&monitor=-&std15= ')
    time.sleep(1.0)
    driver.close()

    return 1


#************************************* MAIN PROGRAM ***********************************************
print "Starting. Current time = ", datetime.datetime.now()
success = GetExteriorCounts()
if success == 1:
    print "Got the data!"
else:
    print "Failed!"
#************************************* END MAIN PROGRAM ***********************************************
