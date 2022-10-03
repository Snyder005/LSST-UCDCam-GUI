#!/usr/bin/env python
#Author: Craig Lage, Andrew Bradshaw, Perry Gee, Daniel Polin,  UC Davis; 
#Date: 17-Feb-15
#Last Revised: 16-Dec-20
# These files contains various subroutines
# needed to run the LSST Simulator
# This class interfaces to the Dylos 1100 Pro Particle Counter.

# Using the Tkinter module for interface design
import matplotlib
matplotlib.use("Agg")
import numpy, time, datetime, sys, fcntl, serial, socket, struct, subprocess, urllib2
from pylab import *
sys.path.append('/sandbox/lsst/lsst/GUI')
import Lakeshore_331
import Email_Warning
#************************************* SUBROUTINES ***********************************************

class Dylos(object):
    def __init__(self):
        self.dylos_device_name='/dev/dylos'
        self.particle_small = 999999
        self.particle_big = 999999
        return

    def Initialize_Serial(self):
        """ Initializes the USB serial bus, using the python serial module"""
        try:
            self.ser = serial.Serial(self.dylos_device_name, 9600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE)
            self.ser.close()
            self.ser.open()
            print "Successfully initialized Dylos Particle Counter\n"
            return
        except:
            print "Failed to initialize Dylos Serial Bus\n"
            return

    def Close_Serial(self):
        """ Closes the USB serial bus, using the python serial module"""
        try:
            self.ser.close()
            print "Successfully closed Dylos Serial Bus\n"
            return
        except:
            print "Failed to close Dylos Serial Bus\n"
            return

    def Check_Communications(self):
        """ Checks whether communication with the Dylos is working"""
        self.comm_status = False
        try:
            self.comm_status = self.ser.isOpen()
        except:
            self.comm_status = False
        return

    def Read_Dylos(self):
        """ Reads the particle count value. """
        self.particle_big = 999999
        self.particle_small = 999999
        try:
            if self.ser.isOpen():
                listen=[]
                self.ser.flushInput()
                while (len(listen) < 2 or len(listen) > 16):
                    time.sleep(0.1)
                    listen = self.ser.readline()
                listen = listen.strip('\r\n').split(',')
                self.particle_small = int(listen[0])
                self.particle_big = int(listen[1])
        except:
            self.particle_small = 999999
            self.particle_big = 999999
        return

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


def GetExteriorCounts():
    ExtTime = []
    Ext = []
    DateTime = datetime.datetime.now()
    try:
        response = urllib2.urlopen('http://www.arb.ca.gov/aqmis2/display.php?download=y&param=PM25HR&units=001&year=2015&report=SITE1YR&statistic=DAVG&site=2143&ptype=aqd&monitor=-')
        data = response.read()
        response.close()
    except:
        return (ExtTime, Ext)
    lines = data.split('\r\n')
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

def ReadTemperatureLog(filename):
    file = open(filename)
    lines = file.readlines()
    file.close()
    Time = []
    Temp_A = []
    Temp_B = []
    for i, line in enumerate(lines):
        if i == 0:
            continue
        else:
            data = line.split()
            Time.append(float(data[0]))
            Temp_A.append(float(data[1]))
            Temp_B.append(float(data[2]))
    return(Time, Temp_A, Temp_B)

def MakePlot(Time, Small, Big, ExtTime, Ext, TempTime, Time_A, Time_B):
    # Moving averages
    Big_Ave = []
    Small_Ave = []
    NAve = 12
    for i in range(len(Big)):
        Big_Ave.append((array(Big[i-NAve+2:i]).sum() + Big[i-1] + Big[i])/NAve + 100.0)
        Small_Ave.append(max(Small[i], 3000.0))
    (year, month, day, hour, min, sec) = JD_to_Date(Time[-1])
    MinTime = max(2457108.0, Time[-1]-9.0)
    MaxTime = MinTime + 10.0
    MinY = 0.0
    MaxY = 7.0
    fig=figure(figsize=(8,10))
    ax1=axes([0.2,0.35,0.7,0.55])
    ax1.set_title("Particle Count Trend - Horizontal Lines are Class 1000")
    ax1.set_xlabel("Time (Julian Day)")
    #ylabel("Log Particles/m^3")
    ax1.text(MinTime-0.9,4.5,"Log Particles/m^3", color='black', rotation = 'vertical')
    ax1.text(MinTime-0.5,3.3,">2.5 $\mu m$", color='green', rotation = 'vertical')
    ax1.text(MinTime-0.5,4.7,">0.5 $\mu m$", color='blue', rotation = 'vertical')
    ax1.set_ylim(MinY,MaxY)
    ax1.set_xlim(MinTime, MaxTime)
    ax1.plot(Time, log10(Small_Ave), marker = 'o', ms = 0.1, color='blue')
    ax1.plot([MinTime, MaxTime],log10([35200, 35200]),color='blue')
    #text(MinTime + 1.0, log10(15000), 'Class 1000 > 0.5 micron', color='blue', fontweight = 'bold')
    ax1.plot(Time, log10(Big_Ave), marker = 'o', ms = 0.1, color='green')
    ax1.plot(ExtTime, log10(Ext), marker = 'o', ms = 0.1, color='red')
    ax1.plot([MinTime, MaxTime],log10([1240, 1240]),color='green')
    #text(MinTime+1.0, log10(600), 'Class 1000 > 2.5 micron', color='green', fontweight = 'bold')
    ax1.text(MinTime+1.0, 1.5, 'Last measurement made at %02d:%02d:%02d on %d/%d/%d'%(hour,min,sec,month,day,year), color='blue', fontweight = 'bold')
    ax1.text(MinTime+1.0, 1.0, 'Exterior air quality from www.arb.ca.gov', color='red', fontweight = 'bold')
    #ax1.text(MinTime+1.0, 0.5, 'Temp_A = %.2f, Temp_B = %.2f'%(Temp_A[-1], Temp_B[-1]), color='blue', fontweight = 'bold')

    # Mark changes to room
    """
    filter_change = Date_to_JD(datetime.datetime(year=2015,month=4,day=14,hour=9,minute=45))
    plot([filter_change,filter_change],[2.0,2.5],color='brown', lw=3)
    text(filter_change-0.5, 1.5, 'F:300 cfm', color='brown')
    filter_change_2 = Date_to_JD(datetime.datetime(year=2015,month=4,day=16,hour=8,minute=27))
    plot([filter_change_2,filter_change_2],[2.0,2.5],color='brown', lw=3)
    text(filter_change_2-0.5, 1.5, 'F:40 cfm', color='brown')
    filter_change_3 = Date_to_JD(datetime.datetime(year=2015,month=4,day=18,hour=12,minute=02))
    plot([filter_change_3,filter_change_3],[2.0,2.5],color='brown', lw=3)
    text(filter_change_3-0.5, 1.5, 'F:300 cfm', color='brown')
    room_air_change_1 = Date_to_JD(datetime.datetime(year=2015,month=4,day=23,hour=13,minute=37))
    plot([room_air_change_1,room_air_change_1],[2.0,2.5],color='brown', lw=3)
    text(room_air_change_1-1.0, 1.5, 'R:125 cfm', color='brown')
    clean_1 = Date_to_JD(datetime.datetime(year=2015,month=4,day=24,hour=14,minute=30))
    plot([clean_1,clean_1],[2.0,2.5],color='brown', lw=3)
    text(clean_1-0.5, 1.8, 'vacuum', color='brown')
    """
    filter_change = Date_to_JD(datetime.datetime(year=2015,month=5,day=5,hour=15,minute=33))
    ax1.plot([filter_change,filter_change],[2.2,2.5],color='brown', lw=3)
    ax1.text(filter_change-0.5, 2.0, 'New F:250 cfm', color='brown')
    enclosure = max(MinTime,Date_to_JD(datetime.datetime(year=2015,month=5,day=15,hour=13,minute=30)))
    ax1.plot([enclosure,enclosure],[2.2,2.5],color='brown', lw=3)
    ax1.text(enclosure-1.0, 2.0, 'Enclosure', color='brown')
    enclosure_2 = max(MinTime,Date_to_JD(datetime.datetime(year=2015,month=5,day=16,hour=17,minute=00)))
    ax1.plot([enclosure_2,enclosure_2],[2.2,2.5],color='brown', lw=3)
    ax1.text(enclosure_2-1.0, 1.75, 'Seal,Clean,130cfm', color='brown')

    # Finish Marks

    for i in range(11):
        time = int(MinTime) + 0.5 + float(i)
        ax1.plot([time,time],[MinY,MaxY],linestyle = 'dotted', color = 'black')

    ax2=axes([0.2,0.1,0.65,0.15])
    ax2.set_title("Temperature Trend")
    ax2.set_xlabel("Time (Julian Day)")
    ax2.set_ylabel("Dewar Temperature (C)", color='blue')
    MinY = -195.0
    MaxY = -192.0
    ax2.set_ylim(MinY,MaxY)
    ax2.set_xlim(MinTime, MaxTime)
    ax2.plot(TempTime, Temp_A, marker = 'o', ms = 0.1, color='blue')

    for i in range(11):
        time = int(MinTime) + 0.5 + float(i)
        ax2.plot([time,time],[MinY,MaxY],linestyle = 'dotted', color = 'black')
        time = time + 13.75 / 24
        if time > 2457151.0 and time < Time[-1]:
            ax2.plot([time, time],[-193.5, -193.0],color='brown', lw=3)
            ax2.text(time-0.30, -193.0, 'Fill', color='brown')

    ax3=ax2.twinx()
    ax3.set_ylim(-140,-95)
    ax3.set_ylabel("CCD Temperature (C)", color='green')
    ax3.plot(TempTime, Temp_B, marker = 'o', ms = 0.1, color='green')

    fig.savefig("particle_graph.png")
    del(fig)
    del(ax1)
    del(ax2)
    return

#************************************* MAIN PROGRAM ***********************************************
dylos = Dylos()
dylos.Initialize_Serial()
lake = Lakeshore_331.Lakeshore()
lake.Initialize_Serial()

(Time, Small, Big) = ReadParticleLog('particle_log.dat')
(ExtTime,Ext) = GetExteriorCounts()
(TempTime, Temp_A, Temp_B) = ReadTemperatureLog('temperature_log.dat')
MakePlot(Time, Small, Big, ExtTime, Ext, TempTime, Temp_A, Temp_B)
lastjd = 0

while True:
    dylos.Read_Dylos()
    jd = Date_to_JD(datetime.datetime.now())
    thisjd = int(jd + 0.5)
    if thisjd != lastjd: # Get new exterior data each day
        (ExtTime,Ext) = GetExteriorCounts()
        lastjd = thisjd 
    out = "%.4f \t \t %d \t \t \t \t %d\n"%(jd, dylos.particle_small*100, dylos.particle_big*100)
    file = open('particle_log.dat', 'a')
    file.write(out)
    file.close()
    (Time, Small, Big) = ReadParticleLog('particle_log.dat')
    lake.Read_Temp()
    if lake.Temp_A > -190.0:
        Email_Warning.Send_Warning('Dewar Temp Warning', 'Warning. Dewar Temp > -190 C')
    out = "%.4f \t \t %.2f \t \t %.2f\n"%(jd, lake.Temp_A, lake.Temp_B)
    file = open('temperature_log.dat', 'a')
    file.write(out)
    file.close()
    (TempTime, Temp_A, Temp_B) = ReadTemperatureLog('temperature_log.dat')
    MakePlot(Time, Small, Big, ExtTime, Ext, TempTime, Temp_A, Temp_B)
    command = 'scp particle_graph.png cslage@physauth.physics.ucdavis.edu:/nfs/physweb-sites/lage.physics.ucdavis.edu/support_files/astro_papers/'
    copygraph = subprocess.Popen(command, shell=True)
    subprocess.Popen.wait(copygraph)
    time.sleep(600)
#************************************* END MAIN PROGRAM ***********************************************
