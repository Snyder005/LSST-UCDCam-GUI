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
    def __init__(self, master):
        self.master = master
        self.lakeshore_device_name='/dev/lakeshore_331'
        self.Temp_A = 999.0
        self.Temp_B = 999.0
        self.Temp_Set = 999.0
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
            print "Successfully initialized Lakeshore Serial Bus, Temp_A = %.2f, Temp_B = %.2f\n"%(self.Temp_A, self.Temp_B)
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
            self.ser.close()
            self.ser.open()
            self.comm_status = self.ser.isOpen()
        except:
            self.comm_status = False
        self.ser.close()
        return

    def Read_Temp(self):
        """ Reads the temperature value. """
        self.Temp_A = 999.0
        self.Temp_B = 999.0
        self.Temp_Set = 999.0
        try:
            self.ser.close()
            self.ser.open()
            if self.ser.isOpen():
                self.ser.flushInput()
                self.ser.write('RDGST?\r\n')
                status = int(self.ser.readline().split()[0])
                if status != 0:
                    self.ser.close()
                    return
                else:
                        time.sleep(0.1)
                        self.ser.flushInput()
                        self.ser.write('SETP?\r\n')
                        self.Temp_Set = float(self.ser.readline().split()[0])
                        time.sleep(0.1)
                        self.ser.flushInput()
                        self.ser.write('CRDG?A\r\n')
                        self.Temp_A = float(self.ser.readline().split()[0])
                        time.sleep(0.1)
                        self.ser.flushInput()
                        self.ser.write('CRDG?B\r\n')
                        self.Temp_B = float(self.ser.readline().split()[0])
                        self.ser.close()
                        return
        except:
            self.ser.close()
            return


