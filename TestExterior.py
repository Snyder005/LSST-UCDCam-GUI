#!/usr/bin/env python
# Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
# Date: 11-Oct-17
# This gest the exterior particle counts and saves them to a file

import numpy, time, datetime, sys, os, serial, struct, subprocess, urllib2
from pylab import *
sys.path.append('/sandbox/lsst/lsst/GUI')

#************************************* SUBROUTINES ***********************************************

def GetExteriorCounts():
    ExtTime = []
    Ext = []
    DateTime = datetime.datetime.now()
    try:
        response = urllib2.urlopen('http://www.arb.ca.gov/aqmis2/display.php?download=y&param=PM25HR&units=001&year=2017&report=SITE1YR&statistic=DAVG&site=2143&ptype=aqd&monitor=-&std15= ')
        data = response.read()
        response.close()
        time.sleep(1.0)
    except Exception as e:
        print "Failed to read Exterior particle counts. Exception of type %s and args = \n"%type(e).__name__, e.args    
        sys.stdout.flush()
        return (ExtTime, Ext)
    lines = data.split('\r\n')
    for line in lines:
        entries = line.split(',')
        print entries
        try:
            date = entries[0].split('-')
            year = int(date[0])
            month = int(date[1])
            day = int(date[2])
            counts = float(entries[3])
            ExtTime.append(Date_to_JD(datetime.datetime(year,month,day,21,43,0)))
            Ext.append(counts / 6.5E-5)
        except:
            continue
    return (ExtTime, Ext)

def Date_to_JD(DateTime):
    # Convert a datetime to Julian Day.
    # Algorithm from 'Practical Astronomy with your Calculator or Spreadsheet', 
    # 4th ed., Duffet-Smith and Zwart, 2011.
    # Assumes the date is after the start of the Gregorian calendar.
    year = DateTime.year
    month = DateTime.month
    day = DateTime.day

    if month == 1 or month == 2:
        yearp = year - 1
        monthp = month + 12
    else:
        yearp = year
        monthp = month

    # Assumes we are after the start of the Gregorian calendar
    A = numpy.trunc(yearp / 100.)
    B = 2 - A + numpy.trunc(A / 4.)
    C = numpy.trunc(365.25 * yearp)
    D = numpy.trunc(30.6001 * (monthp + 1))
    jd = B + C + D + day + 1720994.5

    return jd + (DateTime.hour + DateTime.minute / 60.0 + DateTime.second / 3600.0) / 24.0

def JD_to_Date(jd):
    # Convert a Julian Day to time and date
    jd = jd + 0.5
    F, I = math.modf(jd)
    I = int(I)
    A = math.trunc((I - 1867216.25)/36524.25)
    if I > 2299160:
        B = I + 1 + A - math.trunc(A / 4.)
    else:
        B = I
    C = B + 1524
    D = math.trunc((C - 122.1) / 365.25)
    E = math.trunc(365.25 * D)
    G = math.trunc((C - E) / 30.6001)
    days = C - E + F - math.trunc(30.6001 * G)
    if G < 13.5:
        month = G - 1
    else:
        month = G - 13
    if month > 2.5:
        year = D - 4716
    else:
        year = D - 4715
    days, day = math.modf(days)
    hours = days * 24.
    hours, hour = math.modf(hours)
    mins = hours * 60.
    mins, min = math.modf(mins)
    secs = mins * 60.
    secs, sec = math.modf(secs)
    return (int(year), int(month), int(day), int(hour), int(min), int(sec))


#************************************* MAIN PROGRAM ***********************************************
print "Starting. Current time = ", datetime.datetime.now()
sys.stdout.flush()

(ExtTime,Ext) = GetExteriorCounts()

print Ext
sys.stdout.flush()
#************************************* END MAIN PROGRAM ***********************************************
