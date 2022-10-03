#!/usr/bin/env python
#Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
#Date: 17-Feb-15
# These files contains various subroutines
# needed to run the LSST Simulator
# This class interfaces to the Lakeshore 321 temp controller.

# Using the Tkinter module for interface design
from Tkinter import *
import numpy, time, sys, fcntl, serial, socket, struct

class Lakeshore(object):
    def __init__(self):
        self.lakeshore_device_name='/dev/ttyUSB1'
        self.temp = 999.0
        return

    def Initialize_Serial(self):
        """ Initializes the USB serial bus, using the python serial module"""
        try:
            baudrate = 1200
            timeout = 2000
            self.ser = serial.Serial(self.lakeshore_device_name, baudrate, serial.SEVENBITS, serial.PARITY_ODD, serial.STOPBITS_ONE, timeout)
            self.ser.close()
            self.ser.open()
            self.Read_Temp()
            print "Successfully initialized Lakeshore Serial Bus, Temp = %.1f\n"%self.temp
            return
        except:
            print "Failed to initialize Lakeshore Serial Bus\n"
            return

    def Close_Serial(self):
        """ Closes the USB serial bus, using the python serial module"""
        try:
            self.ser.close()
            print "Successfully closed Lakeshore Serial Bus\n"
            return
        except:
            print "Failed to close Lakeshore Serial Bus\n"
            return

    def Check_Communications(self):
        """ Checks whether communication with the Lakeshore is working"""
        self.comm_status = False
        try:
            self.comm_status = self.ser.isOpen()
        except:
            self.comm_status = False
        return

    def Read_Temp(self):
        """ Reads the temperature value. """
        self.temp = 999.0
        NumTries = 0
        try:
            if self.ser.isOpen():
                self.ser.flushInput()
                self.ser.write('CDAT?\r\n')
                while NumTries <  10:
                    NumTries += 1
                    time.sleep(0.1)
                    if self.ser.inWaiting() == 9:
                        self.temp = float(self.ser.readline().split()[0])
                        return
        except:
            self.temp = 999.0
        return


