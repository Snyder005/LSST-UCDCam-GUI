#!/usr/bin/env python
#Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
#Date: 17-Feb-15
# These files contains various subroutines
# needed to run the LSST Simulator
# This class interfaces to the Dylos 1100 Pro Particle Counter.

import numpy, time, datetime, sys
from pylab import *

#************************************* SUBROUTINES ***********************************************

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
