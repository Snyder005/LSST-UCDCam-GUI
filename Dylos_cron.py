 #!/usr/bin/env python
#Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
#Date: 17-Feb-15
# These files contains various subroutines
# needed to run the LSST Simulator
# This class interfaces to the Dylos 1100 Pro Particle Counter.

# Using the Tkinter module for interface design
import matplotlib
matplotlib.use("Agg")
import numpy, time, datetime, sys, os, serial, struct, subprocess, urllib2
from pylab import *
sys.path.append('/sandbox/lsst/lsst/GUI')
import eolib
import Email_Warning as ew
import Lakeshore_335
import DewarFill
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
            sys.stdout.flush()
            return
        except Exception as e:
            print "Failed to initialize Dylos. Exception of type %s and args = \n"%type(e).__name__, e.args    
            sys.stdout.flush()
            return

    def Close_Serial(self):
        """ Closes the USB serial bus, using the python serial module"""
        try:
            self.ser.close()
            print "Successfully closed Dylos Serial Bus\n"
            sys.stdout.flush()
            return
        except Exception as e:
            print "Failed to close Dylos Serial Bus. Exception of type %s and args = \n"%type(e).__name__, e.args    
            sys.stdout.flush()
            return

    def Check_Communications(self):
        """ Checks whether communication with the Dylos is working"""
        self.comm_status = False
        try:
            self.comm_status = self.ser.isOpen()
        except Exception as e:
            print "Failed to set Dylos Comm Status. Exception of type %s and args = \n"%type(e).__name__, e.args    
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
                print "Succeeded in reading Dylos. Small = %d, Big = %d\n"%(self.particle_small, self.particle_big)
                sys.stdout.flush()
        except Exception as e:
            print "Failed to read Dylos. Exception of type %s and args = \n"%type(e).__name__, e.args    
            sys.stdout.flush()
            self.particle_small = 999999
            self.particle_big = 999999
        return

def CheckIfFileExists(filename):
    try:
        FileSize = os.path.getsize(filename)
        return True
    except (OSError, IOError):
        return False

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

def GetLastNLines(filename, n):
    # Get last n lines of a file
    proc=subprocess.Popen(['tail','-n',str(n),filename], stdout=subprocess.PIPE)
    soutput,sinput=proc.communicate()
    lines = soutput.split('\n')
    lines.pop() # Strip last line, which is empty
    return lines

def GetExteriorCounts():
    ExtTime = []
    Ext = []
    DateTime = datetime.datetime.now()
    file = open("exterior_counts.txt", "r")
    lines = file.readlines()
    file.close()
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
    lines = GetLastNLines(filename, 1500)
    Time = []
    Small = []
    Big = []
    for i, line in enumerate(lines):
        data = line.split()
        Time.append(float(data[0]))
        Small.append(int(data[1]) * cuft_per_cum)
        Big.append(int(data[2]) * cuft_per_cum)
    return(Time, Small, Big)

def ReadTemperatureLog(filename):
    lines = GetLastNLines(filename, 1500)
    Time = []
    Temp_A = []
    Temp_B = []
    for i, line in enumerate(lines):
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
    MinTime = Time[-1]-9.0
    MaxTime = MinTime + 10.0
    MinY = 0.0
    MaxY = 7.0
    figure(figsize=(8,10))
    ax1=axes([0.2,0.35,0.7,0.55])
    ax1.set_title("Particle Count Trend - Horizontal Dashed Lines are Class 1000")
    ax1.set_xlabel("Time (Julian Day)")
    #ylabel("Log Particles/m^3")
    ax1.text(MinTime-0.9,4.5,"Log Particles/m^3", color='black', rotation = 'vertical')
    ax1.text(MinTime-0.5,3.3,">2.5 $\mu m$", color='green', rotation = 'vertical')
    ax1.text(MinTime-0.5,4.7,">0.5 $\mu m$", color='blue', rotation = 'vertical')
    ax1.set_ylim(MinY,MaxY)
    ax1.set_xlim(MinTime, MaxTime)
    ax1.plot(Time, log10(Small_Ave), marker = 'o', ms = 0.1, color='blue')
    ax1.plot([MinTime, MaxTime],log10([35200, 35200]),color='blue',ls='--',lw=2) # Class 1000 line
    #text(MinTime + 1.0, log10(15000), 'Class 1000 > 0.5 micron', color='blue', fontweight = 'bold')
    ax1.plot(Time, log10(Big_Ave), marker = 'o', ms = 0.1, color='green')
    ax1.plot(ExtTime, log10(Ext), marker = 'o', ms = 0.1, color='red')
    ax1.plot([MinTime, MaxTime],log10([1240, 1240]),color='green',ls='--',lw=2) # Class 1000 line
    #text(MinTime+1.0, log10(600), 'Class 1000 > 2.5 micron', color='green', fontweight = 'bold')
    ax1.text(MinTime+1.0, 1.5, 'Last measurement made at %02d:%02d:%02d on %d/%d/%d'%(hour,min,sec,month,day,year), color='blue', fontweight = 'bold')
    ax1.text(MinTime+1.0, 1.0, 'Exterior air quality from www.arb.ca.gov', color='red', fontweight = 'bold')
    #ax1.text(MinTime+1.0, 0.5, 'Temp_A = %.2f, Temp_B = %.2f'%(Temp_A[-1], Temp_B[-1]), color='blue', fontweight = 'bold')

    # Finish Marks
    for i in range(11):
        daytime = int(MinTime) + 0.5 + float(i)
        ax1.plot([daytime,daytime],[MinY,MaxY],linestyle = 'dotted', color = 'black')

    CfgFile = "/sandbox/lsst/lsst/GUI/UCDavis.cfg"
    Temp_to_Fill = float(eolib.getCfgVal(CfgFile,"Temp_to_Fill")) # This is the temp to trigger a fill

    ax2=axes([0.2,0.1,0.65,0.15])
    ax2.set_title("Temperature Trend")
    ax2.set_xlabel("Time (Julian Day)")
    ax2.set_ylabel("Dewar Temperature (C)", color='blue')
    ax2.plot([MinTime,MaxTime],[Temp_to_Fill,Temp_to_Fill],linestyle = 'dotted', color = 'red')
    MinY = -200.0
    MaxY = -195.0
    ax2.set_ylim(MinY,MaxY)
    ax2.set_xlim(MinTime, MaxTime)
    ax2.plot(TempTime, Temp_A, marker = 'o', ms = 0.1, color='blue')

    for i in range(11):
        daytime = int(MinTime) + 0.5 + float(i)
        ax2.plot([daytime,daytime],[MinY,MaxY],linestyle = 'dotted', color = 'black')

    fill_lines = GetLastNLines('fill_log.dat', 10) # Get last 10 fills
    for line in fill_lines:
        plottime = float(line.split()[0])
        fill_time = float(line.split()[1])
        if plottime > MinTime:
            ax2.plot([plottime, plottime],[-197.0, -197.5],color='brown', lw=3)
            ax2.text(plottime-0.30, -195.5, 'Fill', color='brown')
            ax2.text(plottime-0.30, -196.5, '%.0f'%fill_time, color='brown', fontsize=8)
    ax3=ax2.twinx()
    ax3.set_ylim(-140,40)
    ax3.set_xlim(MinTime, MaxTime)
    ax3.set_ylabel("CCD Temperature (C)", color='green')
    ax3.plot(TempTime, Temp_B, marker = 'o', ms = 0.1, color='green')
    NumTries = 0
    while NumTries < 10:
        NumTries += 1
        time.sleep(1.0)
        try:
            savefig("particle_graph.png")
        except:
            continue
    return

def CheckIfStillRunning():
    # This checks if the last cron job is still running.
    # We don't want to keep launching jobs if the last one has hung up
    if CheckIfFileExists("DylosStillRunning"):
        print "Cron Job still running. Quitting\n"
        sys.stdout.flush()
        file = open('DylosStillRunning','r')
        line = file.readline()
        file.close()
        lastminute = int(line.split()[4].split(':')[1])
        currentminute = datetime.datetime.now().minute
        if currentminute - lastminute < 15:
            # Only send a warning the first time it fails so as not to spam inboxes.
            Warning('Dylos cron job appears to have stopped running')
    file = open('DylosStillRunning','w')
    file.write("Job started at "+str(datetime.datetime.now())+" is still running\n")
    file.close()
    return

def ReadAndLogParticles():
    # Handles reading and logging the particle counts
    dylos = Dylos()
    dylos.Initialize_Serial()
    dylos.Read_Dylos()
    jd = Date_to_JD(datetime.datetime.now())
    out = "%.4f \t \t %d \t \t \t \t %d\n"%(jd, dylos.particle_small*100, dylos.particle_big*100)
    file = open('particle_log.dat', 'a')
    file.write(out)
    file.close()
    return

def ReadTempsAndHandleDewarFill(dewarfill):
    # Reads the temperatures and manages the Dewar fill
    lake = Lakeshore_335.Lakeshore('dummy')
    lake.Initialize_Serial()
    lake.Read_Temp()
    NumTries = 0
    # Added the following loop to prevent occasional bogus 999.0 readings
    while lake.Temp_A > 900.0 and NumTries < 5:
        time.sleep(0.5)
        lake.Read_Temp()
        NumTries += 1

    jd = Date_to_JD(datetime.datetime.now())
    out = "%.4f \t \t %.2f \t \t %.2f\n"%(jd, lake.Temp_A, lake.Temp_B)
    file = open('temperature_log.dat', 'a')
    file.write(out)
    file.close()

    # Dewar Autofill
    CfgFile = "/sandbox/lsst/lsst/GUI/UCDavis.cfg"
    # This file has the parameters that control the autofill
    Dewar_is_Cold = int(eolib.getCfgVal(CfgFile,"Dewar_is_Cold"))
    # Change this flag to turn off automatic Dewar fill and E-Mail warnings
    # 1 = Autofill enabled; 0 = autofill disabled
    Temp_to_Fill = float(eolib.getCfgVal(CfgFile,"Temp_to_Fill")) # This is the temp to trigger a fill
    Min_Fill_Time = float(eolib.getCfgVal(CfgFile,"Min_Fill_Time")) # This is the minimum fill time
    Fill_Time_Limit = float(eolib.getCfgVal(CfgFile,"Fill_Time_Limit")) # This is the maximum fill time
    Overflow_Temp_Limit = float(eolib.getCfgVal(CfgFile,"Overflow_Temp_Limit"))
    # This is the temp on the overflow monitor that stops the fill

    if Dewar_is_Cold == 1 and lake.Temp_A > Temp_to_Fill:
        (TempTime, Temp_A, Temp_B) = ReadTemperatureLog('temperature_log.dat')
        if Temp_A[-2] > Temp_to_Fill - 0.2: # 1-Aug-17: Corrected error. Now looking at last reading, not current reading.
            lake.Read_Temp()
            NumTries = 0
            # Added the following loop to prevent occasional bogus 999.0 readings
            while lake.Temp_A > 900.0 and NumTries < 5:
                time.sleep(0.5)
                lake.Read_Temp()
                NumTries += 1
            if lake.Temp_A > Temp_to_Fill:
                # This sequence ensures that a fill only happens if
                # we have three readings in a row over the set point.
                # Now we also check that a fill has not occurred in the last 3 hours
                fill_lines = GetLastNLines('fill_log.dat', 1) # Get last fill
                if jd - float(fill_lines[0].split()[0]) > 0.125:
                    start_fill_status = dewarfill.StartFill()
                    time.sleep(0.1)
                    if start_fill_status:
                        time.sleep(0.1)
                        startfill = time.time()
                        elapsed = 0.0
                        temp = Overflow_Temp_Limit + 1.0
                        difftemp = 0.0
                        overflowfile = open('overflow_log.dat','a')
                        time.sleep(0.1)
                        # while elapsed < Fill_Time_Limit and difftemp < 0.8 and temp > Overflow_Temp_Limit: OLD
                        while elapsed < Min_Fill_Time or (elapsed < Fill_Time_Limit and temp > Overflow_Temp_Limit):
                            # Stop the fill when we reach time limit or detect LN2 overflow
                            # or detect that the valve is no longer open (open:state=True)
                            lasttemp = temp
                            [state, temp] = dewarfill.MeasureOverFlowTemp()
                            difftemp = lasttemp - temp
                            # When liquid hits the overflow sensor, the temp drops rapidly
                            # we will terminate the fill if the difference between the latest
                            # temp reading and the last temp reading is > 0.8 degrees
                            # of if the temp reading drops below Overflow_Temp_Limit
                            # 1-Jul-19: added a condition to wait at least 90 seconds before
                            # checking the overflow condition.
                            # 1-Jul-19: Also removed difftemp condition.
                            line = "Temp at %s is %f\n"%(datetime.datetime.now(),temp)
                            overflowfile.write(line)
                            elapsed = time.time() - startfill
                            if state:
                                valve_state = "Open"
                            if not state:
                                # Break out of the loop if the valve doesn't stay open
                                valve_state = "Closed"
                                break
                            time.sleep(0.25)
                        if state:
                            dewarfill.LogFill(fill_time=elapsed)
                        print "Terminated fill loop. Elapsed = %f, Overflow temp = %f, Valve state = %s\n"%(elapsed,temp,valve_state) 
                        sys.stdout.flush()
                        overflowfile.close()
                    stop_fill_status = dewarfill.StopFill()
                    NumTries = 0
                    while not stop_fill_status and NumTries < 5: # Try 5 times to make sure valve is closed
                        time.sleep(0.5)
                        stop_fill_status = dewarfill.StopFill()
                        NumTries += 1
                    if not stop_fill_status:
                        Warning('Failure terminating Dewar fill!!!!')

    if Dewar_is_Cold == 1 and lake.Temp_A > -190.0:
        Warning('Warning. Dewar Temp > -190 C')
    return

#   This routine both sends a warning to the email list in Email_Warning
#   and also writes the warning to disk under the file named "send_warning"
def Warning(warning):
    try:
        subject = "Dylos Warning issued " + time.asctime()
        w_file = open('send_warning', 'w')
        w_file.write(subject + ":: ")
        w_file.write(warning)
        w_file.close()
        #comment out this call, as emailing has been moved to opal
        #ew.Send_Warning(subject, warning)
    except:
        pass

#************************************* MAIN PROGRAM ***********************************************

print "Starting. Current time = ", datetime.datetime.now()
sys.stdout.flush()
jd1 = Date_to_JD(datetime.datetime.now())

CheckIfStillRunning() # Make sure there isn't another job still running.

ReadAndLogParticles()
(Time, Small, Big) = ReadParticleLog('particle_log.dat')

dewarfill = DewarFill.DewarFill('dummy')
try:
    ReadTempsAndHandleDewarFill(dewarfill)
except Exception as e:
    print "Failure in Temp read or Dewar Fill. Exception of type %s and args = \n"%type(e).__name__, e.args    
    sys.stdout.flush()
    dewarfill.StopFill() # In case of failure, make sure dewar fill valve is closed
(TempTime, Temp_A, Temp_B) = ReadTemperatureLog('temperature_log.dat')
(ExtTime,Ext) = GetExteriorCounts()

MakePlot(Time, Small, Big, ExtTime, Ext, TempTime, Temp_A, Temp_B)

# Delete file which indicates we are still running.
command = "rm DylosStillRunning"
delfile = subprocess.Popen(command, shell=True)
subprocess.Popen.wait(delfile)
jd2 = Date_to_JD(datetime.datetime.now())
elapsed = (jd2-jd1)*86400
print "Current time = ", datetime.datetime.now()
print "Done. Elapsed time = %f\n"%elapsed
sys.stdout.flush()

#  To replace the cron job on opal,
#  copy the particle graph to the http server on omega
command = 'ssh opal.llan scp /sandbox/lsst/lsst/GUI/particles/particle_graph.png dls:/var/www/html/storm'
copygraph = subprocess.Popen(command, shell=True)
subprocess.Popen.wait(copygraph)

      
#************************************* END MAIN PROGRAM ***********************************************
