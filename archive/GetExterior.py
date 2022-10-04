#!/usr/bin/env python
# Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
# Date: 1-Nov-17
# This gets the exterior particle counts and saves them to a file

import sys, time, datetime, urllib2
from selenium import webdriver
sys.path.append('/usr/local/bin')
#************************************* SUBROUTINES ***********************************************

def GetExteriorCounts():
    year = str(datetime.datetime.now().year)
    try:
        driver = webdriver.PhantomJS()
        driver.get('https://www.arb.ca.gov/aqmis2/display.php?download=y&param=PM25HR&units=001&year=%s&report=SITE1YR&statistic=DAVG&site=2143&ptype=aqd&monitor=-&std15= '%year)
        time.sleep(1.0)
        response = urllib2.urlopen('https://www.arb.ca.gov/aqmis2/display.php?download=y&param=PM25HR&units=001&year=%s&report=SITE1YR&statistic=DAVG&site=2143&ptype=aqd&monitor=-&std15= '%year)
        time.sleep(1.0)
        data = response.read()
        driver.close()
        response.close()
    except Exception as e:
        print "Failed to read Exterior particle counts. Exception of type %s and args = \n"%type(e).__name__, e.args    
        sys.stdout.flush()
        return 0
    lines = data.split('\r\n')
    file = open("exterior_counts.txt","r")
    loglines = file.readlines()
    file.close()
    logdates = []
    for line in loglines:
        logdates.append(line.split(',')[0])
    file = open("exterior_counts.txt","a")
    for line in lines:
        items = line.split(',')
        date = items[0]
        char = list(date)
        if len(char) > 1:
            if char[0] == '2' and char[1] == '0':
                counts = items[3]
                char_counts = list(counts)
                if date not in logdates and len(char_counts) > 0:
                    file.write(line+'\r\n')
    file.close()
    return 1

#************************************* MAIN PROGRAM ***********************************************
print "Starting. Current time = ", datetime.datetime.now()
NumTries = 0
success = 0
while (success == 0 and NumTries < 5):
    success = GetExteriorCounts()
    if success == 1:
        print "Got the data!"
    else:
        print "Failed!"
        NumTries += 1
        time.sleep(5.0)
#************************************* END MAIN PROGRAM ***********************************************
