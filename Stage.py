#!/usr/bin/env python
#Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
#Date: 7-Jan-15
# These files contains various subroutines
# needed to run the LSST Simulator
# This class sets the Tkinter frame for moving the XYZ stage
#  as well as reading out the optical encoders

# Using the Tkinter module for interface design
from Tkinter import *
import numpy, time, sys, fcntl, serial, socket, struct

class Stage(object):
    def __init__(self, master):
        self.master = master
        #*** XYZ stage stepper motor settings ***
        self.POS_NAME = ['x', 'y', 'z']
        self.STEPPER_NAME = ['I1M', 'I3M', 'I2M']
        self.stage_device_name='/dev/stage_control'
        #*** Encoder Settings ***
        # For optical encoders which read stage position
        # Various constants.  See /usr/local/src/pci_quad04/pci-quad04/RegMapPCI-QUAD04.pdf
        self.ENCODER_NAME = ['/dev/quad04/channel0_1', '/dev/quad04/channel0_3', '/dev/quad04/channel0_2']
        # These are ordered (x, y, z)
        self.LOAD_CMD_REG = 0x7701 # Loads the command register
        self.X4  = 0x38 # Set Counter Mode Register (CMR)
        # Selects Binary counting, Normal count mode, X4 scaling (readout in um)
        self.TRAN_PR_CNTR = 0x8 # Transfer PR register to 24 bit counter
        self.IOR_DISABLE_INDEX = 0x45 # Sets Input/Output Control register (IOR)
        # Selects Load Cntr, A/B Enable gate, FLG1 Carry, FLG2 Borrow, 

        self.set_pos = [0,0,0]
        self.read_pos = [0,0,0]
        return

    def Initialize_Serial(self):
        """ Initializes the USB serial bus, using the python serial module"""
        for NumTries in range(5):
            try:
                self.ser = serial.Serial(self.stage_device_name)
                self.ser.close()
                self.ser.open()
                print "Successfully initialized Stage Serial Bus\n"
                return
            except Exception as e:
                print "Failure initializing Stage serial bus. Exception of type %s and args = \n"%type(e).__name__, e.args    
                time.sleep(0.1)
                continue

        print "Failed to initialize Stage Serial Bus\n"
        return

    def Close_Serial(self):
        """ Closes the USB serial bus, using the python serial module"""
        try:
            self.ser.close()
            print "Successfully closed Stage Serial Bus\n"
            return
        except Exception as e:
            print "Failed to close Stage serial bus. Exception of type %s and args = \n"%type(e).__name__, e.args    
            return
    
    def Initialize_Encoders(self):
        """Initializes the optical encoders and sets the read positions to zeros"""
        for NumTries in range(5):
            try:
                self.fd_channel = []
                for i in range(3):
                    self.fd_channel.append(open(self.ENCODER_NAME[i], "r+b"))
                    fcntl.ioctl(self.fd_channel[i], self.LOAD_CMD_REG, self.X4) 
                    fcntl.ioctl(self.fd_channel[i], self.LOAD_CMD_REG, self.IOR_DISABLE_INDEX) 
                    self.fd_channel[i].write(b'\x00\x00\x00') 
                    # Write zeros to 24 bit PR register
                    fcntl.ioctl(self.fd_channel[i], self.LOAD_CMD_REG, self.TRAN_PR_CNTR) 
                    # Transfers the PR register to the counter
                    self.read_pos[i] = 0
                print "Successfully initialized Encoders\n"
                return
            except Exception as e:
                print "Failure initializing optical encoders. Exception of type %s and args = \n"%type(e).__name__, e.args    
                time.sleep(0.1)
                continue

        print "Failed to initialize Encoders\n"
        return

    def Close_Encoders(self):
        """Closes the optical encoders"""
        try:
            for i in range(3):
                self.fd_channel[i].close()
            print "Successfully closed Encoders\n"
            return
        except Exception as e:
            print "Failure to close optical encoders. Exception of type %s and args = \n"%type(e).__name__, e.args    
            return

    def Check_Communications(self):
        """ Checks whether communication with the motors (USB) and encoders (PCI) are working"""
        self.serial_status = False
        try:
            self.serial_status = self.ser.isOpen()
        except Exception as e:
            print "No communication to stage serial bus. Exception of type %s and args = \n"%type(e).__name__, e.args    
            self.serial_status = False
        self.encoder_status = False
        try:
            self.encoder_status = True
            for i in range(3):
                value = self.fd_channel[i].read(3)+b'\x00' 
                # read the 24 bit register (3 bytes) and add a fourth byte 
                # to make it an integer.
                signed_value = struct.unpack("=I", value)[0] 
                if signed_value < 0 or signed_value > 2**24:
                    self.encoder_status = False
                    break
        except Exception as e:
            print "No communication to optical encoders. Exception of type %s and args = \n"%type(e).__name__, e.args    
            self.encoder_status = False
        self.comm_status = self.serial_status and self.encoder_status
        return

    def ReInitialize_Encoders(self):
        """ Reset the encoder values to zero"""
        for i in range(3):
            self.fd_channel[i].write(b'\x00\x00\x00') 
            # Write zeros to 24 bit PR register
            fcntl.ioctl(self.fd_channel[i], self.LOAD_CMD_REG, self.TRAN_PR_CNTR) 
            # Transfers the PR register to the counter
            self.read_pos[i] = 0
        return

    def Read_Encoders(self):
        """ Reads the encoder values. Loops until the encoders have settled down"""
        max_diff = 100
        while max_diff > 1:
            max_diff = 0
            time.sleep(0.2)
            for i in range(3):
                last_read_pos = self.read_pos[i]
                value = self.fd_channel[i].read(3)+b'\x00' 
                # read the 24 bit register (3 bytes) and add a fourth byte 
                # to make it an integer.
                signed_value = struct.unpack("=I", value)[0] 
                # Convert byte string to int
                if signed_value > 2**23:
                    signed_value = signed_value - 2**24
                self.read_pos[i] = signed_value
                max_diff = max(max_diff, abs(last_read_pos - self.read_pos[i]))
            return

    def Move_Stage(self):
        """Moves the stage a number of stepper pulses given by the set_pos value [x, y, z]"""
        for i in range(3):
            if self.set_pos[i] == 0:
                continue
            print "Moving stage %s by %s steps\n"%(self.POS_NAME[i], self.set_pos[i])
            self.ser.write('F,C'+self.STEPPER_NAME[i]+str(self.set_pos[i])+',R')
            time.sleep(0.5)
        time.sleep(0.5)
        return

    def GUI_ReInitialize_Encoders(self):
        """ Reset the encoder values to zero"""
        print "Re-initializing Encoders"
        self.ReInitialize_Encoders()
        self.GUI_Write_Encoder_Values()
        return

    def GUI_Write_Encoder_Values(self):
	"""A target for the encoder position labels on the GUI"""
        for i in range(3):
            self.encoder_text[i].set("%8s microns"%str(self.read_pos[i]))
        return

    def GUI_move(self, axis):
	"""A target for the move buttons on the GUI"""
        self.set_pos = [0,0,0]
        entry = self.coo_ent[axis].get()
        if entry == "":
            entry = "0"
        try:
            entry = int(entry)
        except Exception as e:
            print "Invalid entry. Exception of type %s and args = \n"%type(e).__name__, e.args    
            return
        if entry > 50000 or entry < -50000:
            print "Stage movement too large"
            return
        self.set_pos[axis] = entry
        print "move %s = %d"%(self.POS_NAME[axis], self.set_pos[axis])
        self.Move_Stage()
        self.Read_Encoders()
        self.GUI_Write_Encoder_Values()
        return

    def Define_Frame(self):
        """ Stage position frame in the Tk GUI. Defines buttons and their location"""
        self.frame=Frame(self.master, relief=GROOVE, bd=4)
        self.frame.grid(row=0,column=1,rowspan=2,columnspan=2)
        frame_title = Label(self.frame,text="Stage Control",relief=RAISED,bd=2,width=24, bg="light yellow",font=("Times", 16))
        frame_title.grid(row=0, column=1)
        self.encoder_text = [] # These hold the stage position as read by the encoders
        self.coo_ent = [] # These hold the coordinate entry values
        but = []
        encoder_display = []
        for i in range(3):
            self.coo_ent.append(Entry(self.frame, justify="center", width=12))
            but.append(Button(self.frame, text="Move %s (relative)"%self.POS_NAME[i], width=12,command=lambda axis=i:self.GUI_move(axis)))
            self.encoder_text.append(StringVar())
            encoder_display.append(Label(self.frame,textvariable=self.encoder_text[i],relief=SUNKEN,bd=1, width=20))
            self.coo_ent[i].grid(row=i+1,column=0)
            self.coo_ent[i].focus_set()
            but[i].grid(row=i+1,column=1)
            encoder_display[i].grid(row=i+1,column=2)
            self.encoder_text[i].set("%8s microns"%str(self.read_pos[i]))
        zero_encoders_button = Button(self.frame, text="Re-Initialize Encoders", width=20, command=self.GUI_ReInitialize_Encoders)
        zero_encoders_button.grid(row=5,column=1)
        return


