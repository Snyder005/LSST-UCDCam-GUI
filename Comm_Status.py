#!/usr/bin/env python
#Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
#Date: 14-Jan-15
# These files contains various subroutines
# needed to run the LSST Simulator
# This class sets the Tkinter frame for checking the communication and turning things on

# Using the Tkinter module for interface design
from Tkinter import *
import numpy, time, sys, fcntl, serial, socket, struct


class Comm_Status():
    def __init__(self, master, stage, sphere, camera, lakeshore, bk, dewarfill):
        self.master = master
        self.stage = stage
        self.sphere = sphere
        self.camera = camera
        self.lakeshore = lakeshore
        self.bk = bk
        self.dewarfill = dewarfill
        return

    def Check_Communications(self):
        """ Checks all connections, refers to the other classes """
        self.bk.Check_Communications()
        self.stage.Check_Communications()
        self.sphere.Check_Communications()
        self.camera.Check_Communications()
        self.lakeshore.Check_Communications()
        self.dewarfill.Check_Communications()
        return

    def GUI_Check_Communications(self):
        """Provides a target for the GUI button to check all connections. Updates labels with info"""
        print "Checking Comm Status"
        self.Check_Communications()
        self.serial_text.set("Serial Status="+str(self.stage.serial_status))
        self.light_text.set("Light Socket Status="+str(self.sphere.light_socket_status))
        self.shutter_text.set("Shutter Socket Status="+str(self.sphere.shutter_socket_status))
        self.encoder_text.set("Encoder Status="+str(self.stage.encoder_status))
        self.camera_text.set("Camera Status="+str(self.camera.comm_status))
        self.bss_relay_text.set("BSS Relay Status="+str(self.camera.bss_relay_status))
        self.lakeshore_text.set("Lakeshore Status="+str(self.lakeshore.comm_status)+" CCD Temp = "+str(self.lakeshore.Temp_B))
        self.bk_text.set("BK Precision Status="+str(self.bk.comm_status))
        self.dewar_text.set("Dewar Fill Status="+str(self.dewarfill.comm_status))
        return


    def Define_Frame(self):
        """This defines the buttons and labels in the Tk GUI Communication Status frame"""
        self.frame=Frame(self.master, relief=GROOVE, bd=4)
        self.frame.grid(row=0,column=4,rowspan=2,columnspan=2)
        frame_title = Label(self.frame,text="Communication Status",relief=RAISED,bd=2,width=20, bg="light yellow",font=("Times", 16))
        frame_title.grid(row=0, column=1)

        check_status_but = Button(self.frame, text="Check Comm Status", width=24,command=self.GUI_Check_Communications)
        check_status_but.grid(row=1,column=0)

        start_comm_but = Button(self.frame, text="Start All Communications", width=24,command=self.GUI_Start_All)
        start_comm_but.grid(row=1,column=1)

        close_comm_but = Button(self.frame, text="Close All Communications", width=24,command=self.GUI_Close_All)
        close_comm_but.grid(row=1,column=2)

        initialize_serial_but = Button(self.frame, text="Initialize Serial", width=16,command=self.stage.Initialize_Serial)
        initialize_serial_but.grid(row=2,column=0)
        self.serial_text=StringVar()
        serial_out = Label(self.frame,textvariable=self.serial_text)
        self.serial_text.set("Serial Status=False")
        serial_out.grid(row=3,column=0)

        initialize_light_but = Button(self.frame, text="Initialize Light", width=16,command=self.sphere.Initialize_Light_Socket)
        initialize_light_but.grid(row=2,column=1)
        self.light_text=StringVar()
        light_out = Label(self.frame,textvariable=self.light_text)
        self.light_text.set("Light Socket Status=False")
        light_out.grid(row=3,column=1)

        initialize_bk_but = Button(self.frame, text="Initialize BK Precision", width=16,command=self.bk.Initialize_Serial)
        initialize_bk_but.grid(row=4,column=1)
        self.bk_text=StringVar()
        bk_out = Label(self.frame,textvariable=self.bk_text)
        self.bk_text.set("BK Precision Status=False")
        bk_out.grid(row=5,column=1)

        initialize_shutter_but = Button(self.frame, text="Initialize Shutter", width=16,command=self.sphere.Initialize_Shutter_Socket)
        initialize_shutter_but.grid(row=2,column=2)
        self.shutter_text=StringVar()
        shutter_out = Label(self.frame,textvariable=self.shutter_text)
        self.shutter_text.set("Shutter Socket Status=False")
        shutter_out.grid(row=3,column=2)

        initialize_encoder_but = Button(self.frame, text="Initialize Encoder", width=16,command=self.stage.Initialize_Encoders)
        initialize_encoder_but.grid(row=4,column=0)
        self.encoder_text=StringVar()
        encoder_out = Label(self.frame,textvariable=self.encoder_text)
        self.encoder_text.set("Encoder Status=False")
        encoder_out.grid(row=5,column=0)
        
        initialize_camera_but = Button(self.frame, text="Initialize Camera", width=16,command=self.camera.sixteen_ch_setup)
        initialize_camera_but.grid(row=4,column=2)
        self.camera_text=StringVar()
        camera_out = Label(self.frame,textvariable=self.camera_text)
        self.camera_text.set("Camera Status=False")
        camera_out.grid(row=5,column=2)
        
        initialize_lakeshore_but = Button(self.frame, text="Initialize Lakeshore", width=16,command=self.lakeshore.Initialize_Serial)
        initialize_lakeshore_but.grid(row=6,column=0)
        self.lakeshore_text=StringVar()
        lakeshore_out = Label(self.frame,textvariable=self.lakeshore_text)
        self.lakeshore_text.set("Lakeshore Status=False")
        lakeshore_out.grid(row=7,column=0)

        initialize_dewar_but = Button(self.frame, text="Initialize Dewar Fill", width=16,command=self.dewarfill.Check_Communications)
        initialize_dewar_but.grid(row=6,column=1)
        self.dewar_text=StringVar()
        dewar_out = Label(self.frame,textvariable=self.dewar_text)
        self.dewar_text.set("Dewar Fill Status="+str(self.dewarfill.comm_status))
        dewar_out.grid(row=7,column=1)

        initialize_bss_relay_but = Button(self.frame, text="Initialize BSS Relay", width=16,command=self.camera.Initialize_BSS_Relay)
        initialize_bss_relay_but.grid(row=6,column=2)
        self.bss_relay_text=StringVar()
        bss_relay_out = Label(self.frame,textvariable=self.bss_relay_text)
        self.bss_relay_text.set("BSS_Relay Status=False")
        bss_relay_out.grid(row=7,column=2)
        return 

    def Start_All(self):
        """ Opens all connections"""
        self.stage.Initialize_Serial()
        self.lakeshore.Initialize_Serial()
        self.sphere.Initialize_Light_Socket()
        self.sphere.Initialize_Shutter_Socket()
        self.stage.Initialize_Encoders()
        self.camera.sixteen_ch_setup()
        self.camera.Initialize_BSS_Relay()
        self.bk.Initialize_Serial()
        self.dewarfill.Check_Communications()
        return

    def Close_All(self):
        """ Opens all connections"""
        self.stage.Close_Serial()
        self.lakeshore.Close_Serial()
        self.sphere.Close_Light_Socket()
        self.sphere.Close_Shutter_Socket()
        self.stage.Close_Encoders()
        self.camera.Close_BSS_Relay()
        self.bk.Close_Serial()
        return

    def GUI_Start_All(self):
        """ Opens all connections"""
        self.Start_All()
        self.GUI_Check_Communications()
        return

    def GUI_Close_All(self):
        """ Closes all connections"""
        self.Close_All()
        self.GUI_Check_Communications()
        return

    def Final_Close_All(self):
        """ Closes all connections at the end"""
        self.Close_All()
        return


