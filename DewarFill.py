#!/usr/bin/env python
#Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
#Date: 17-Feb-15
# These files contains various subroutines
# needed to run the LSST Simulator
# This class interfaces to the Phidgets relay athat controls the Dewar LN2 fill.

# Using the Tkinter module for interface design
from Tkinter import *
import numpy, time, datetime, sys, subprocess
from astropy.time import Time
from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Devices.InterfaceKit import InterfaceKit

#************************************* SUBROUTINES ***********************************************

class DewarFill(object):
    def __init__(self, master):
        self.master = master
        self.fill_log_name='/sandbox/lsst/lsst/GUI/particles/fill_log.dat'
        self.valve = InterfaceKit()
        self.comm_status = False
        self.ov_temp = 999.0
        self.valve_state = "Closed"
        return

    def Check_Communications(self):
        # Checks on communications status with the Dewar Fill relay
        self.comm_status = False
        try:
            self.valve.openPhidget(431944) # Serial number 431944 is the Dewar valve Phidget
            self.valve.waitForAttach(10000)
            if self.valve.isAttached() and self.valve.getSerialNum() == 431944:
                self.comm_status = True
            self.valve.closePhidget()
            print "Successfully initialized DewarFill Relay\n" 
            sys.stdout.flush()
        except PhidgetException as e:
            print("Phidget Exception %i: %s" % (e.code, e.details))
            print "Failed to initialize DewarFill Relay\n" 
            sys.stdout.flush()
            self.valve.closePhidget()
            return

    def StartFill(self):
        # Opens the Dewar fill valve
        try:
            self.valve.openPhidget(431944) # Serial number 431944 is the Dewar valve Phidget
            self.valve.waitForAttach(1000)
            if self.valve.isAttached() and self.valve.getSerialNum() == 431944:
                time.sleep(0.1)
                self.valve.setOutputState(0,True) # This opens the valve
                self.valve.setOutputState(1,True)
                time.sleep(2.0)
                self.valve.closePhidget()
            self.valve.openPhidget(431944) # Serial number 431944 is the Dewar valve Phidget
            self.valve.waitForAttach(1000)
            if self.valve.isAttached() and self.valve.getSerialNum() == 431944:
                time.sleep(0.1)
                state0 = self.valve.getOutputState(0)
                state1 = self.valve.getOutputState(1)
                if state0 and state1:
                    time.sleep(0.1)
                    self.valve.closePhidget()
                    print "Successfully initiated Dewar fill at ", datetime.datetime.now()
                    sys.stdout.flush()
                    time.sleep(0.1)
                    self.valve.closePhidget()
                    time.sleep(0.1)
                    return True
                else:
                    print "Error 1 in initiating Dewar fill at ", datetime.datetime.now()
                    sys.stdout.flush()
                    self.valve.closePhidget()
                    return False

        except PhidgetException as e:
            print "Error 2 in initiating Dewar fill at ", datetime.datetime.now()
            print("Phidget Exception %i: %s" % (e.code, e.details))
            sys.stdout.flush()
            self.valve.closePhidget()
            return False

    def StopFill(self):
        # Closes the Dewar fill valve
        try:
            self.valve.openPhidget(431944) # Serial number 431944 is the Dewar valve Phidget
            self.valve.waitForAttach(1000)
            if self.valve.isAttached() and self.valve.getSerialNum() == 431944:
                time.sleep(0.1)
                self.valve.setOutputState(0,False) # This closes the valve
                self.valve.setOutputState(1,False)
                time.sleep(1.0)
                self.valve.closePhidget()
            self.valve.openPhidget(431944) # Serial number 431944 is the Dewar valve Phidget
            self.valve.waitForAttach(1000)
            if self.valve.isAttached() and self.valve.getSerialNum() == 431944:
                time.sleep(0.1)
                state0 = self.valve.getOutputState(0)
                state1 = self.valve.getOutputState(1)
                if not state0 and not state1:
                    time.sleep(0.1)
                    self.valve.closePhidget()
                    print "Successfully terminated Dewar fill at ", datetime.datetime.now()
                    sys.stdout.flush()
                    time.sleep(0.1)
                    self.valve.closePhidget()
                    time.sleep(0.1)
                    return True
                else:
                    print "Error 1 in terminating Dewar fill at ", datetime.datetime.now()
                    sys.stdout.flush()
                    self.valve.closePhidget()
                    return False

        except PhidgetException as e:
            print "Error 2 in terminating Dewar fill at ", datetime.datetime.now()
            print("Phidget Exception %i: %s" % (e.code, e.details))
            sys.stdout.flush()
            self.valve.closePhidget()
            return False


    def MeasureOverFlowTemp(self):
        # Measures the temperature in the overflow cup
        # returns both the valve state and the temperature
        try:
            self.valve.openPhidget(431944) # Serial number 431944 is the Dewar valve Phidget
            self.valve.waitForAttach(1000)
            if self.valve.isAttached() and self.valve.getSerialNum() == 431944:
                sensor = self.valve.getSensorValue(3)
                NumTries = 0
                while sensor < 0.01 and NumTries < 5:
                    time.sleep(0.1)
                    sensor = self.valve.getSensorValue(3)
                    NumTries += 1
                self.ov_temp = sensor * 0.2222 - 61.111
                state0 = self.valve.getOutputState(0)
                state1 = self.valve.getOutputState(1)
                state = state0 and state1
                if state:
                    self.valve_state = "Open"
                if not state:
                    self.valve_state = "Closed"
                self.valve.closePhidget()
                return [state, self.ov_temp]
            else:
                self.valve.closePhidget()
                return [False, 999.0]
        except PhidgetException as e:
            print("Phidget Exception %i: %s" % (e.code, e.details))
            sys.stdout.flush()
            self.valve.closePhidget()
            return [False, 999.0]

    def MeasureOverFlowTempGUI(self):
        # Measures the temperature in the overflow cup
        [state, temp] = self.MeasureOverFlowTemp()
        if state:
            self.valve_state = "Open"
        if not state:
            self.valve_state = "Closed"
        self.ovtemp_text.set("Overflow Temp="+str(self.ov_temp)+" Valve State="+self.valve_state)
        return

    def LogFill(self, fill_time=0.0):
        # Logs the Dewar Fill
        jd = Time(datetime.datetime.now(), format='datetime').jd
        out = "%.4f   %.1f\n"%(jd, fill_time)
        file = open(self.fill_log_name, 'a')
        file.write(out)
        file.close()
        time.sleep(0.1)
        return

    def Define_Frame(self):
        """ Dewar Fill frame in the Tk GUI. Defines buttons and their location"""
        self.frame=Frame(self.master, relief=GROOVE, bd=4)
        self.frame.grid(row=3,column=4,rowspan=1,columnspan=2)
        frame_title = Label(self.frame,text="Manual Dewar Fill",relief=RAISED,bd=2,width=36, bg="light yellow",font=("Times", 16))
        frame_title.grid(row=0, column=0)
        fill_but = Button(self.frame, text="Start Dewar Fill", width=36, command=self.StartFill)
        fill_but.grid(row=1,column=0)
        stop_but = Button(self.frame, text="Stop Dewar Fill", width=20, command=self.StopFill)
        stop_but.grid(row=2,column=0)
        log_but = Button(self.frame, text="Log Dewar Fill", width=20, command=self.LogFill)
        log_but.grid(row=3,column=0)
        ovtemp_but = Button(self.frame, text="Check Overflow Temp", width=16,command=self.MeasureOverFlowTempGUI)
        ovtemp_but.grid(row=4,column=0)
        self.ovtemp_text=StringVar()
        ovtemp_out = Label(self.frame,textvariable=self.ovtemp_text)
        self.ovtemp_text.set("Overflow Temp="+str(self.ov_temp)+" Valve State="+self.valve_state)
        ovtemp_out.grid(row=5,column=0)
        return
