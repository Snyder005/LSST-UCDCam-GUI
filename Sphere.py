#!/usr/bin/env python
#Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
#Date: 14-Jan-15
# These files contains various subroutines
# needed to run the LSST Simulator
# This class sets the Tkinter frame for communicating with the Labsphere
#  as well as the light switch and variable aperture (VA) motor


# Using the Tkinter module for interface design
from Tkinter import *
import numpy, time, sys, fcntl, serial, socket, struct

class Sphere(object):
    def __init__(self, master):
        self.master = master
        socket.setdefaulttimeout(0.5)# Timeout if no connection after 0.5 seconds
        #*** Light & photodiode settings ***
        self.light_IP = '192.168.1.100'
        self.light_tcp_portnum = 51344
        self.buffer_size = 1024

        #*** Variable Aperture settings ***
        self.VA_TCP_IP = '192.168.1.200'
        self.VA_TCP_PORT = 4000
        self.VA_BUFFER_SIZE = 1024
        accel_value = '15' #Standard acceleration
        decel_value = '15' #Standard deceleration
        velocity_value = '1.1' #Standard velocity
        current_value = '0.2' #Standard current
        magnification_value = '3' #Standard scale

        self.Value_list = [('AC',accel_value), ('MR',magnification_value), ('DE',decel_value), ('VE',velocity_value), ('CC', current_value)]
        # Sets shutter to proper settings
        self.Tolerance = 0.05 # Checks that settings are equal to what was requested 
                         # within this tolerance.
        self.light_intensity = 0.0
                         
        return

    def Initialize_Light_Socket(self):
        """ Initializes the light socket over Ethernet"""
        for NumTries in range(3):
            try:
                self.light_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
                self.light_socket.connect((self.light_IP, self.light_tcp_portnum))
                print "Successfully initialized Light Socket\n"
                return
            except Exception as e:
                print "Failure to initialize light socket. Exception of type %s and args = \n"%type(e).__name__, e.args    
                time.sleep(0.1)
                continue
        print "Failed to initialize Light Socket\n"
        return

    def Close_Light_Socket(self):
        """ Closes the light socket over Ethernet"""
        try:
            self.light_socket.close()
            print "Successfully closed Light Socket\n"
            return
        except Exception as e:
            print "Failure to close light socket. Exception of type %s and args = \n"%type(e).__name__, e.args    
            return
    
    def Initialize_Shutter_Socket(self):
        # Initializes the shutter socket over Ethernet
        # And sets the parameters (speed, acceleration, etc) to the proper values
        for NumTries in range(3):
            try:
                self.shutter_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.shutter_socket.connect((self.VA_TCP_IP, self.VA_TCP_PORT))
                for (Name,Value) in self.Value_list:
                    self.shutter_socket.send("%s\r"%(Name+Value))
                    time.sleep(0.1)
                    self.shutter_socket.send("%s\r"%(Name))
                    val = float(self.shutter_socket.recv(self.VA_BUFFER_SIZE).split('=')[1])
                    print Name, Value, val
                    test_tolerance = abs((val - float(Value)) / float(Value))
                    if test_tolerance < self.Tolerance:
                        print "Successfully set parameter "+Name+" to value "+Value+". Measured value = "+str(val)
                    else:
                        print "Failed to set parameter "+Name+" to value "+Value
                        print "Set-up failed.  Exiting."
                        self.shutter_socket.close()
                        return
                print "Successfully initialized Shutter Socket\n"
                return
            except Exception as e:
                print "Failure to initialize shutter socket. Exception of type %s and args = \n"%type(e).__name__, e.args    
                time.sleep(0.1)
                continue

        print "Failed to initialize Shutter Socket\n"
        return

    def Close_Shutter_Socket(self):
        """ Closes the shutter socket over Ethernet"""
        try:
            self.shutter_socket.close()
            print "Successfully closed Shutter Socket\n"
            return
        except Exception as e:
            print "Failure to close shutter socket. Exception of type %s and args = \n"%type(e).__name__, e.args    
            return

    def Check_Communications(self):
        # Checks on communications staus
        self.light_socket_status = False
        try:
            test_IP = self.light_socket.getpeername()[0]
            if test_IP == self.light_IP:
                self.light_socket_status = True
        except Exception as e:
            print "Light socket not communicating. Exception of type %s and args = \n"%type(e).__name__, e.args    
            self.light_socket_status = False

        self.shutter_socket_status = False
        try:
            test_IP = self.shutter_socket.getpeername()[0]
            if test_IP == self.VA_TCP_IP:
                self.shutter_socket_status = True
        except Exception as e:
            print "Shutter socket not communicating. Exception of type %s and args = \n"%type(e).__name__, e.args    
        self.comm_status = self.light_socket_status and self.shutter_socket_status
        return


    def Turn_Light_On(self):
        # Turns the light on
        print "Turning light on - 4 second delay for stabilization."
        self.light_socket.send("PS2~1\r")
        self.master.after(4000, self.Read_Photodiode)
        return

    def Turn_Light_Off(self):
        # Turns the light off
        print "Turning light off - 8 second delay for stabilization."
        self.light_socket.send("PS2~0\r")
        self.master.after(8000, self.Read_Photodiode)
        return

    def Final_Light_Off(self):
        # Turns the light off at program exit without updating photodiode current
        print "Turning light off"
        self.light_socket.send("PS2~0\r")
        return

    def VA_Drive_Shutter(self, Move_value):
        # Moves the shutter to a value specified by a Move_value
        # Move_value is a number of stepper motor pulses
        # 12000 = open all the way
            self.shutter_socket.send("DL\r")
            DL_Status = float(self.shutter_socket.recv(self.VA_BUFFER_SIZE).split("=")[1])
            if DL_Status != 1.0:
                    print "DL value not equal to 1. Failed shutter move. Exiting."
                    sys.exit()
            print "DL_Status = ",DL_Status

            self.shutter_socket.send("%s\r"%('DI'+str(Move_value)))
            self.shutter_socket.send("FL\r")

            Move_Success = False
            for NumTries in range(20):
                    time.sleep(0.5)
                    self.shutter_socket.send("RS\r")
                    Status = self.shutter_socket.recv(self.VA_BUFFER_SIZE)
                    print "Status = ", Status
                    if Status == 'R\r':
                            Move_Success = True
                            break
            self.shutter_socket.send("RV\r")
            RV_Status = int(self.shutter_socket.recv(self.VA_BUFFER_SIZE).split('=')[1])
            if RV_Status != 223:
                    print "RV value not equal to 223. Failed shutter move. Exiting."
                    sys.exit()
            if Move_Success:
                    print "Successfully moved shutter as requested"
            else:
                    print "Number of status tests exceeded.  Failed shutter move. Exiting."
                    sys.exit()
            return

    def VA_Calculate_Shutter_Position(self, light_intensity):
        """ Calculates the required shutter position (in %) to give the desired light intensity (in %).
	 Uses I = A + B tanh(C s + D), where s is the shutter position. Constants come from fit to photometer data"""
        A = 4.58586028
        B = 4.56817782
        C = 0.06850201
        D = -3.25073115
        Ap = A / (A + B)
        Bp = B / (A + B)
        s = (numpy.arctanh((light_intensity / 100.0 - Ap) / Bp) - D) / C

        if light_intensity < 1.0:
            print "Light intensity not accurate for intensities < 1%.\n"
            return s
        elif light_intensity >99:
            print "Light intensity not accurate for intensities >99%.  Opening shutter all the way.\n"
            return 100.0
        else:
            return s

    def VA_Set_Light_Intensity(self, light_intensity):
        """ Opens the shutter a specified amount given the input light intensity value.  Assumes 0.0 < Value < 100."""
        print "LightIntensity = %f"%light_intensity 
        if light_intensity < 0.0 or light_intensity > 100.0:
            print "Light Intensity value not between 0 and 100. Exiting"
            sys.exit()

        self.VA_Drive_Shutter(12000)
        # This opens the shutter all the way
        time.sleep(0.5)

        sp = self.VA_Calculate_Shutter_Position(light_intensity)
        # This linearizes the non-linearity of the shutter
        Shutter_Position = int(12000 * sp / 100) - 12000
        self.VA_Drive_Shutter(Shutter_Position)
        # This opens the shutter the requested amount
        time.sleep(0.5)
        self.light_intensity=light_intensity
        return

    def Read_Photodiode(self):
        """ Reads the photodiode current and returns the value in amps"""
        self.light_socket.send("D\r")
        dummy_val = self.light_socket.recv(100)
        time.sleep(0.2)
        self.light_socket.send("D\r")
        self.diode_current = float(self.light_socket.recv(100))
        self.diode_out_text.set(str(self.diode_current))
        time.sleep(0.1)
        return

    def GUI_Set_Light_Intensity(self):
	""" A target for the GUI button to set light intensity"""
        print "Setting Light Intensity"
        self.light_intensity=float(self.light_intensity_ent.get())
        self.VA_Set_Light_Intensity(self.light_intensity)
        self.master.after(300, self.Read_Photodiode)
        return

    def Define_Frame(self):
        """Defines the buttons Lights and aperture frame in the Tk GUI"""
        self.frame=Frame(self.master, relief=GROOVE, bd=4)
        self.frame.grid(row=2,column=4,rowspan=1,columnspan=2)
        frame_title = Label(self.frame,text="Illumination Sphere Control",relief=RAISED,bd=2,width=24, bg="light yellow",font=("Times", 16))
        frame_title.grid(row=0, column=1)

        lighton_but = Button(self.frame,text="Light On",width=10,command=self.Turn_Light_On)
        lighton_but.grid(row=0,column=0)
        lightoff_but = Button(self.frame,text="Light Off",width=10,command=self.Turn_Light_Off)
        lightoff_but.grid(row=1,column=0)
        self.light_intensity_ent = Entry(self.frame, justify="center")
        self.light_intensity_ent.grid(row=1,column=1)
        self.light_intensity_ent.focus_set()
        self.diode_out_text = StringVar()
        diode_out = Label(self.frame,textvariable=self.diode_out_text)
        diode_out.grid(row=2,column=1)
        self.diode_out_text.set('Diode Current')
        light_intensity_but = Button(self.frame, text="Set Light Intensity(%)", width=20,command=self.GUI_Set_Light_Intensity)
        light_intensity_but.grid(row=1,column=2)

        updatepd_but=Button(self.frame,text="Update Photodiode Current",command=self.Read_Photodiode)
        updatepd_but.grid(row=2,column=0)
        return



