#!/usr/bin/env python
#Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
#Date: 17-Feb-15
# These files contains various subroutines
# needed to run the LSST Simulator
# This class interfaces to the Dylos 1100 Pro Particle Counter.

# Using the Tkinter module for interface design
import matplotlib
matplotlib.use("Agg")
import numpy, time, datetime, sys, fcntl, serial, socket, struct, subprocess, urllib2
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

def ReadParticleLog(filename):
    cuft_per_cum = (39.37/12.0)**3
    file = open(filename)
    lines = file.readlines()
    file.close()
    Time = []
    Small = []
    Big = []
    for i, line in enumerate(lines):
        if i == 0:
            continue
        else:
            data = line.split()
            Time.append(float(data[0]))
            Small.append(int(data[1]) * cuft_per_cum)
            Big.append(int(data[2]) * cuft_per_cum)
    return(Time, Small, Big)

def GetExteriorCounts():
    DateTime = datetime.datetime.now()
    response = urllib2.urlopen('http://www.arb.ca.gov/aqmis2/display.php?download=y&param=PM25HR&units=001&year=2015&report=SITE1YR&statistic=DAVG&site=2143&ptype=aqd&monitor=-')
    data = response.read()
    response.close()
    lines = data.split('\r\n')
    ExtTime = []
    Ext = []
    for line in lines:
        entries = line.split(',')
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

def MakeRegressionPlot(Time, Small, ExtTime, Ext):

    NTimes = 21
    MinTime = 2457112
    MaxTime = MinTime + NTimes - 1
    Times = zeros([NTimes],int)
    Small_Ave = zeros([NTimes])
    Exts = zeros([NTimes])
    for i,time in enumerate(range(MinTime, MaxTime+1)):
        Times[i] = time
        for j,exttime in enumerate(ExtTime):
            if int(exttime+0.5) == time:
                Exts[i] = Ext[j]
        small = 0.0
        numsmalls = 0
        for j,smalltime in enumerate(Time):
            if int(smalltime) == time and smalltime - time < 0.4:
                small += Small[j]
                numsmalls += 1
        if numsmalls != 0:
            small /= numsmalls
        Small_Ave[i] = small
    suptitle("Particle Count Correlations")
    subplots_adjust( wspace=0.5)
    subplot(1,2,1)
    title("Trends")
    plot(Times, Small_Ave, label = "Interior counts (0:00-10:00) >0.5 micron")
    plot(Times, Exts, label = "Exterior counts")
    xlabel("Time (JD)")
    ylabel("Particle counts (Particles/m^3)")
    legend(prop={'size':6})
    subplot(1,2,2)
    title("Correlations")
    scatter(Small_Ave, Exts)
    xlabel("Interior Counts")
    ylabel("Exterior Counts")
    xticks([0.0, 200000.0, 400000.0]) 
    show()
    #for i in range(NTimes):
    #    print "Time = %d, Small_Ave = %f, Ext = %f"%(Times[i], Small_Ave[i], Exts[i])
    savefig("regression.png")
    return

#************************************* MAIN PROGRAM ***********************************************
(Time, Small, Big) = ReadParticleLog('particle_log.dat')
(ExtTime,Ext) = GetExteriorCounts()
MakeRegressionPlot(Time, Small, ExtTime, Ext)
#************************************* END MAIN PROGRAM ***********************************************
