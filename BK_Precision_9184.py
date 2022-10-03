#!/usr/bin/env python
#Author: Craig Lage;
#Date: 25-Jan-16
# These files contains various subroutines
# needed to run the LSST Simulator
# This class interfaces to the BK Precision DC Power Supply used to apply back bias to the CCD

# Using the Tkinter module for interface design
from Tkinter import *
import numpy, time, sys, fcntl, serial, socket, struct

class BK_Precision_9184(object):
    def __init__(self, master):
        self.bk_device_name='/dev/bk_precision_9184'
        self.voltage = 0.0
        self.current = 0.0
        self.voltage_limit = 75.0
        self.current_limit = 0.001
        self.BB_on = False
        return

    def Initialize_Serial(self):
        """ Initializes the USB serial bus, using the python serial module"""
        try:
            baudrate = 57600
            timeout = 500
            self.ser = serial.Serial(self.bk_device_name, baudrate, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout)
            self.ser.close()
            self.ser.open()
            if self.ser.isOpen():
                self.ser.flushInput()
                self.ser.write('OUT:LIM:VOLT %.3f\r\n'%self.voltage_limit)
                time.sleep(0.1)
                self.ser.write('OUT:LIM:CURR %.3f\r\n'%self.current_limit)
                time.sleep(0.1)
                self.ser.flushInput()
                self.ser.write('SYS:ERR?\r\n')
                time.sleep(0.1)
                status = int(self.ser.readline().split()[0])
                if status == 0:
                    self.comm_status = True
                    self.bbias_off()
                    self.Read_Voltage()
                    print "Successfully initialized BK Precision Back-Bias supply\n"
                    return
                else:
                    print "Failed to initialize BK Precision Back-Bias supply\n"
                    return
        except Exception as e:
            print "Failed to initialize BK Precision Back-Bias supply. Exception of type %s and args = \n"%type(e).__name__, e.args    
            return

    def Close_Serial(self):
        """ Closes the USB serial bus, using the python serial module"""
        try:
            self.ser.close()
            print "Successfully closed BK Precision Back-Bias supply\n"
            return
        except Exception as e:
            print "Failed to close BK Precision Back-Bias supply. Exception of type %s and args = \n"%type(e).__name__, e.args    
            return

    def Check_Communications(self):
        """ Checks whether communication with the BK Precision is working"""
        self.comm_status = False
        try:
            self.ser.close()
            self.ser.open()
            if self.ser.isOpen():
                self.ser.flushInput()
                self.ser.write('SYS:ERR?\r\n')
                time.sleep(0.1)
                status = int(self.ser.readline().split()[0])
                if status == 0:
                    self.comm_status = True
                    return
                else:
                    self.ser.close()
                    return
        except Exception as e:
            print "No communication to BK Precision Back-Bias supply. Exception of type %s and args = \n"%type(e).__name__, e.args    
            self.ser.close()
            return

    def Read_Voltage(self):
        """ Reads the voltage and current values. """
        self.voltage = -999.0
        self.current = -999.0
        try:
            if self.ser.isOpen():
                self.ser.flushInput()
                time.sleep(0.1)
                self.ser.write('MEAS:VOLT?\r\n')
                time.sleep(0.1)
                self.voltage = float(self.ser.readline().split()[0])
                time.sleep(0.1)
                self.ser.flushInput()
                self.ser.write('MEAS:CURR?\r\n')
                time.sleep(0.1)
                self.current = float(self.ser.readline().split()[0])
                return
            else:
                self.ser.close()
                return
        except Exception as e:
            print "No communication to BK Precision Back-Bias supply. Exception of type %s and args = \n"%type(e).__name__, e.args    
            self.ser.close()
            return

    def Set_Voltage(self, volts):
            """ Sets the voltage and current values. """
            if volts > self.voltage_limit or volts < 0.0:
                print "Requested back bias voltage exceeds limits! Must be a positive number < %f volts.  Nothing done. \n"%self.voltage_limit
                return
                
            self.voltage = -999.0
            self.current = -999.0
            try:
                if self.ser.isOpen():
                    self.ser.write('SOUR:VOLT %.3f\r\n'%volts)
                    self.Read_Voltage()
                    print "Set Voltage Vbb to -%.2f volts"%volts # Note minus sign!
                    return
                else:
                    self.ser.close()
                    return
            except Exception as e:
                print "No communication to BK Precision Back-Bias supply. Exception of type %s and args = \n"%type(e).__name__, e.args    
                self.ser.close()
                return

    def bbias_on(self):
            """ Turns the back bias on """
            self.voltage = -999.0
            self.current = -999.0
            try:
                if self.ser.isOpen():
                    self.ser.write('OUT ON\r\n')
                    self.Read_Voltage()
                    self.BB_on = True
                    return
                else:
                    self.ser.close()
                    return
            except Exception as e:
                print "No communication to BK Precision Back-Bias supply. Exception of type %s and args = \n"%type(e).__name__, e.args    
                self.ser.close()
                return

    def bbias_off(self):
            """ Turns the back bias off """
            self.voltage = -999.0
            self.current = -999.0
            try:
                if self.ser.isOpen():
                    self.ser.flushInput()
                    self.ser.write('OUT OFF\r\n')
                    self.Read_Voltage()
                    self.BB_on = False
                    return
                else:
                    self.ser.close()
                    return
            except Exception as e:
                print "No communication to BK Precision Back-Bias supply. Exception of type %s and args = \n"%type(e).__name__, e.args    
                self.ser.close()
                return
