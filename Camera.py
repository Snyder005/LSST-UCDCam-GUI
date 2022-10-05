#!/usr/bin/env python
#Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
#Date: 12-May-15
# These files contains various subroutines
# needed to run the LSST Simulator
# This class sets the Tkinter frame for controlling the camera. Only basic operations included at the moment


# Using the Tkinter module for interface design
from Tkinter import *
import numpy, time, sys, fcntl, serial, socket, struct
import os, signal, subprocess, datetime
import eolib, ucdavis2lsst
from Phidgets.Devices.InterfaceKit import InterfaceKit

# New imports
from org.lsst.ccs.scripting import CCS
from java.time import Duration
from ccs import proxies

CLEARDELAY = 0.07

fp = CCS.attachProxy("focal-plane")
if agentName != "focal-plane":
   fp = CCS.attachProxy(agentName) # re-attach to ccs subsystem
imageTimeout = 60.0

class Camera(object):
    def __init__(self, master, stage, sphere, lakeshore, bk):
        self.stop_exposures = False
        self.master = master
        self.stage = stage
        self.sphere = sphere
        self.bk = bk
        self.lakeshore = lakeshore
        self.vbb = 0.0
        this_file = os.path.abspath(__file__)
        this_dir = os.path.dirname(this_file)
        CfgFile = os.path.join(this_dir, 'config', 'UCDavis.cfg')
        if self.CheckIfFileExists(CfgFile):
            self.CfgFile = CfgFile
        else:
            print "Configuration file %s not found. Exiting.\n"%CfgFile
            sys.exit()
            return
        self.edtsaodir = eolib.getCfgVal(self.CfgFile,"EDTSAO_DIR")
        self.EDTdir = eolib.getCfgVal(self.CfgFile,"EDT_DIR")
        self.vendor = eolib.getCfgVal(self.CfgFile,"CCD_MANU").strip()
        self.ccd_sern = eolib.getCfgVal(self.CfgFile,"CCD_SERN").strip()
        if not (self.vendor == "ITL" or self.vendor == "E2V"):
            print "Vendor not recognized.  Exiting."
            sys.exit()
        self.fitsfilename = "dummy.fits" # Just a dummy - not really used
        self.relay = InterfaceKit()
        return 

    def CheckIfFileExists(self, filename):
        try:
            FileSize = os.path.getsize(filename)
            return True
        except OSError:
            return False

    def Check_Communications(self):
        """Checks on communications status with the camera, called by the communications frame/class"""
        self.comm_status = False
        (stdoutdata, stderrdata) = self.runcmd([self.edtsaodir+"/fclr"])
        if stdoutdata.split()[1] == 'done' and stderrdata == '':
            self.comm_status = True
        self.bss_relay_status = False
        self.relay.openPhidget(403840) # Serial number 403840 is the Vbb control Phidgets relay
        self.relay.waitForAttach(10000)
        if (self.relay.isAttached() and self.relay.getSerialNum() == 403840):
            self.bss_relay_status = True
        self.relay.closePhidget()
        return

    def Dummy(self):
        # Dummy operation for testing
        return

    def Expose(self):
        #Calls exp_acq script or dark_acq script, depending on exposure type.
        now = datetime.datetime.now()
        timestamp = "%4d%02d%02d%02d%02d%02d"%(now.year,now.month,now.day,now.hour,now.minute,now.second)
        sensor_id = self.sensor_id_ent.get()
        exptime = self.time_ent.get()
        test_type = self.test_type.get()
        image_type = self.image_type.get()
        mask_type = self.mask_type.get()
        sequence_num = self.sequence_num_ent.get()
        filter=self.filter.get()

        fits_header_data = {'ExposureTime' : exptime, 'TestType' : test_type, 'ImageType' : image_type}
        self.master.update()
        if image_type in ['light', 'flat', 'spot']:
            self.exp_acq(exptime=exptime, fits_header_data=self.fits_header_data)
        elif image_type == 'dark':
            self.dark_acq(exptime=exptime, fits_header_data=self.fits_header_data)
        elif image_type == 'bias':
            # A bias exposure is just a dark exposure with 0 time.
            self.dark_acq(exptime=0.0, fits_header_data=self.fits_header_data)
        else:
            print "Image type not recogized.  Exposure not done."
            return
        try:
            self.sphere.Read_Photodiode()
            mondiode = self.sphere.diode_current
            srcpwr = self.sphere.light_intensity
            self.lakeshore.Read_Temp()
            self.stage.Read_Encoders()
            # Add other things here(temp, etc. when they are available)
#            ucdavis2lsst.fix(self.fitsfilename, self.CfgFile, sensor_id, mask_type, test_type, image_type, sequence_num, exptime, filter, srcpwr, mondiode, \
#                             self.lakeshore.Temp_A, self.lakeshore.Temp_B, self.lakeshore.Temp_Set, stage_pos = self.stage.read_pos)
        except Exception as e:
            print "Fits file correction failed! Exception of type %s and args = \n"%type(e).__name__, e.args    
            print "File %s is not LSST compliant"%self.fitsfilename
        return

    def MultiExpose(self):
        #Launches a series of exposures
        numinc = int(self.numinc_ent.get())
        start_sequence_num = int(self.start_sequence_num_ent.get())
        num_per_increment = int(self.numperinc_ent.get())
        dither_radius = int(self.dither_radius_ent.get())
        if num_per_increment < 1 or num_per_increment > 1000:
            print "Number of exposures per increment must be an integer between 1 and 1000.  Exposures not done."
            self.master.update()
            return
        increment_type = self.increment_type.get()
        increment_value = self.increment_value_ent.get()
        delay_value = float(self.delay_ent.get())
        print "Multiple Exposures will start in %.1f seconds. Number of Increments = %d, NumPerInc = %d, StartNum = %d, Type = %s, Increment Value = %s"%(delay_value,numinc,num_per_increment,start_sequence_num,increment_type, increment_value)
        self.master.update()
        time.sleep(delay_value) # Delay to allow you to turn off the lights

        if increment_type == "None":
            for exposure_counter in range(numinc):
                for sub_counter in range(num_per_increment):
                    seq_num = start_sequence_num + num_per_increment * exposure_counter + sub_counter
                    self.sequence_num_ent.delete(0,END)
                    self.sequence_num_ent.insert(0,"%03d"%seq_num)
                    if self.stop_exposures:
                        print "Stopping Exposures based on user input"
                        self.master.update()
                        self.stop_exposures = False
                        return
                    else:
                        self.Expose()

        elif increment_type == "X":
            for exposure_counter in range(numinc):
                self.stage.Read_Encoders()
                self.stage.GUI_Write_Encoder_Values()
                for sub_counter in range(num_per_increment):
                    seq_num = start_sequence_num + num_per_increment * exposure_counter + sub_counter
                    self.sequence_num_ent.delete(0,END)
                    self.sequence_num_ent.insert(0,"%03d"%seq_num)
                    if self.stop_exposures:
                        print "Stopping Exposures based on user input"
                        self.master.update()
                        self.stop_exposures = False
                        return
                    else:
                        self.Expose()
                self.stage.set_pos = [int(increment_value), 0, 0]
                self.stage.Move_Stage()

        elif increment_type == "Y":
            for exposure_counter in range(numinc):
                self.stage.Read_Encoders()
                self.stage.GUI_Write_Encoder_Values()
                for sub_counter in range(num_per_increment):
                    seq_num = start_sequence_num + num_per_increment * exposure_counter + sub_counter
                    self.sequence_num_ent.delete(0,END)
                    self.sequence_num_ent.insert(0,"%03d"%seq_num)
                    self.Expose()
                self.stage.set_pos = [0, int(increment_value), 0]
                self.stage.Move_Stage()

        elif increment_type == "Z":
            for exposure_counter in range(numinc):
                self.stage.Read_Encoders()
                self.stage.GUI_Write_Encoder_Values()
                for sub_counter in range(num_per_increment):
                    seq_num = start_sequence_num + num_per_increment * exposure_counter + sub_counter
                    self.sequence_num_ent.delete(0,END)
                    self.sequence_num_ent.insert(0,"%03d"%seq_num)
                    if self.stop_exposures:
                        print "Stopping Exposures based on user input"
                        self.master.update()
                        self.stop_exposures = False
                        return
                    else:
                        self.Expose()
                self.stage.set_pos = [0, 0, int(increment_value)]
                self.stage.Move_Stage()

        elif increment_type == "Exp(Log)":
            for exposure_counter in range(numinc):
                for sub_counter in range(num_per_increment):
                    seq_num = start_sequence_num + num_per_increment * exposure_counter + sub_counter
                    self.sequence_num_ent.delete(0,END)
                    self.sequence_num_ent.insert(0,"%03d"%seq_num)
                    exptime = self.time_ent.get()
                    if dither_radius > 0 and num_per_increment > 1:
                        #x_dither = int(dither_radius * (-1.0 + 2.0 * numpy.random.rand()))
                        #y_dither = int(dither_radius * (-1.0 + 2.0 * numpy.random.rand()))
                        #self.stage.set_pos = [x_dither, y_dither, 0]
                        x_dither = int(dither_radius)
                        y_dither = 0.0
                        self.stage.set_pos = [x_dither, y_dither, 0]
                        self.stage.Move_Stage()
                        self.stage.Read_Encoders()
                        self.stage.GUI_Write_Encoder_Values()
                    if self.stop_exposures:
                        print "Stopping Exposures based on user input"
                        self.master.update()
                        self.stop_exposures = False
                        return
                    else:
                        self.Expose()

                # Exposure time increments in log steps
                self.time_ent.delete(0,END)
                self.time_ent.insert(0,str(float(increment_value) * float(exptime)))

        elif increment_type == "Exp(Linear)":
            for exposure_counter in range(numinc):
                for sub_counter in range(num_per_increment):
                    seq_num = start_sequence_num + num_per_increment * exposure_counter + sub_counter
                    self.sequence_num_ent.delete(0,END)
                    self.sequence_num_ent.insert(0,"%03d"%seq_num)
                    exptime = self.time_ent.get()
                    if dither_radius > 0 and num_per_increment > 1:
                        #x_dither = int(dither_radius * (-1.0 + 2.0 * numpy.random.rand()))
                        #y_dither = int(dither_radius * (-1.0 + 2.0 * numpy.random.rand()))
                        #self.stage.set_pos = [x_dither, y_dither, 0]
                        x_dither = int(dither_radius)
                        y_dither = 0.0
                        self.stage.set_pos = [x_dither, y_dither, 0]
                        self.stage.Move_Stage()
                        self.stage.Read_Encoders()
                        self.stage.GUI_Write_Encoder_Values()
                    if self.stop_exposures:
                        print "Stopping Exposures based on user input"
                        self.master.update()
                        self.stop_exposures = False
                        return
                    else:
                        self.Expose()
                # Exposure time increments in linear steps
                self.time_ent.delete(0,END)
                self.time_ent.insert(0,str(float(increment_value) + float(exptime)))

        elif increment_type == "Cooling Curve":
            Starting_Temp = 20.0
            Final_Temp = -100.0
            Target_Temps = numpy.linspace(Starting_Temp, Final_Temp, numinc)
            self.lakeshore.Read_Temp()

            for exposure_counter in range(numinc):
                Target_Temp = Target_Temps[exposure_counter]
                # Wait until it cools to the target level
                while self.lakeshore.Temp_B > Target_Temp:
                    self.master.update()
                    if self.stop_exposures:
                        print "Stopping Exposures based on user input"
                        self.master.update()
                        self.stop_exposures = False
                        return
                    self.lakeshore.Read_Temp()
                    time.sleep(5.0)                   

                # First take num_per_increment - 1 bias frames, then 1 dark
                for sub_counter in range(num_per_increment - 1):
                    seq_num = start_sequence_num + num_per_increment * exposure_counter + sub_counter
                    self.sequence_num_ent.delete(0,END)
                    self.sequence_num_ent.insert(0,"%03d"%seq_num)
                    self.image_type.set("bias")
                    if self.stop_exposures:
                        print "Stopping Exposures based on user input"
                        self.master.update()
                        self.stop_exposures = False
                        return
                    else:
                        self.Expose()
                seq_num = start_sequence_num + num_per_increment * exposure_counter + num_per_increment - 1
                self.sequence_num_ent.delete(0,END)
                self.sequence_num_ent.insert(0,"%03d"%seq_num)
                self.image_type.set("dark")
                if self.stop_exposures:
                    print "Stopping Exposures based on user input"
                    self.master.update()
                    self.stop_exposures = False
                    return
                else:
                    self.Expose()
		
        elif increment_type == "Light Intensity":
            for exposure_counter in range(numinc):
                self.sphere.light_intensity=float(self.sphere.light_intensity_ent.get())
                self.sphere.VA_Set_Light_Intensity(self.sphere.light_intensity)
                time.sleep(10)
                self.sphere.Read_Photodiode()
                for sub_counter in range(num_per_increment):
                    seq_num = start_sequence_num + num_per_increment * exposure_counter + sub_counter
                    self.sequence_num_ent.delete(0,END)
                    self.sequence_num_ent.insert(0,"%03d"%seq_num)
                    if dither_radius > 0 and num_per_increment > 1:
                        x_dither = int(dither_radius * (-1.0 + 2.0 * numpy.random.rand()))
                        y_dither = int(dither_radius * (-1.0 + 2.0 * numpy.random.rand()))
                        self.stage.set_pos = [x_dither, y_dither, 0]
                        self.stage.Move_Stage()
                        self.stage.Read_Encoders()
                        self.stage.GUI_Write_Encoder_Values()
                    if self.stop_exposures:
                        print "Stopping Exposures based on user input"
                        self.master.update()
                        self.stop_exposures = False
                        return
                    else:
                        self.Expose()
                # Change light intensity of sphere with increment
                new_intensity = self.sphere.light_intensity + float(increment_value)
                if new_intensity < 0.0 or new_intensity > 100.0:
                    print "Intensity outside of limits.  Quitting exposures."
                    self.master.update()
                    return
                self.sphere.light_intensity_ent.delete(0,END)
                self.sphere.light_intensity_ent.insert(0,str(new_intensity))

	# Makes focus curves, at increasing intensities if desired. 
	###!!!! Assumes stages have been zeroed at location of focus curve minimum!!!!
	### Backlash distance ~35 steps ###
        elif increment_type == "V-curve (Linear)":
            for exposure_counter in range(numinc):
		self.stage.Read_Encoders()             # read encoders to get current pos (should be zero, but if it isn't, ok)
		print "Current pos:" +str(self.stage.read_pos)
		zpos_cur=self.stage.read_pos[2]/2.5    # divide microns by 2.5 to get steps
		zmov_dist=-zpos_cur-dither_radius-45   # move stage back by the dither radius, plus some distance to account for backlash to overshoot
		self.stage.set_pos = [0,0,zmov_dist]   # prepare move constant list
		print "Moving in z: "+str(zmov_dist)
		self.stage.Move_Stage()		       # move
		self.stage.Read_Encoders()             # read
		print "Current pos:" +str(self.stage.read_pos)
		zpos_cur=self.stage.read_pos[2]/2.5    # divide by 2.5 to get steps 
		zmov_dist=numpy.abs(zpos_cur+dither_radius) + 36  # move the stage forward by the difference between cur. pos. and (neg)dither radius, plus calc. backlash
		self.stage.set_pos = [0,0,zmov_dist]   # prepare move constant list
		print "Moving in z: "+str(zmov_dist)
		self.stage.Move_Stage()                # move
		self.stage.Read_Encoders()
		self.stage.GUI_Write_Encoder_Values()
		print "Current pos:" +str(self.stage.read_pos)
                self.master.update()
                for sub_counter in range(num_per_increment):     
                    seq_num = start_sequence_num + num_per_increment * exposure_counter + sub_counter
                    self.sequence_num_ent.delete(0,END)
                    self.sequence_num_ent.insert(0,"%03d"%seq_num)
                    exptime = self.time_ent.get()
                    if dither_radius > 0 and num_per_increment > 1:
			self.stage.Read_Encoders()
			zpos_cur=self.stage.read_pos[2]/2.5
			ndithers_left=num_per_increment-sub_counter   # the number of exposures left to reach other end of dither radius
                        x_dither = int(dither_radius/4. * (-1.0 + 2.0 * numpy.random.rand()))
                        y_dither = int(dither_radius/4. * (-1.0 + 2.0 * numpy.random.rand()))
			z_dither = int(numpy.ceil(numpy.abs(zpos_cur-dither_radius)/ndithers_left))   #round up so that it never rounds down
			foo_dithers=[x_dither,y_dither,z_dither]
			self.stage.Read_Encoders()
			for i in range(3):
			    thepos=self.stage.read_pos[i]/2.5
			    if abs(thepos-foo_dithers[i])>1.2*dither_radius:
				print "Dither radius exceeded, moving back stage #"+str(i)
				if i==3: foo_dithers[i]=int(-1.*thepos + numpy.sign(thepos)*35) # purposeful movement of z-stage back by offset from zero + backlash
				else:    foo_dithers[i]=int(-1.*thepos)

			    print "Position: " +str(thepos)+", Requested move: "+str(foo_dithers[i])		
                            self.master.update()
                        self.stage.set_pos = foo_dithers
                        self.stage.Move_Stage()
                        self.stage.Read_Encoders()
                        self.stage.GUI_Write_Encoder_Values()
                    if self.stop_exposures:
                        print "Stopping Exposures based on user input"
                        self.master.update()
                        self.stop_exposures = False
                        return
                    else:
                        self.Expose()
		# return the stage to zero
		self.stage.Read_Encoders()             # read encoders to get current pos (should be zero, but if it isn't, ok)
		zpos_cur=self.stage.read_pos[2]/2.5    # divide microns by 2.5 to get steps
		zmov_dist=-zpos_cur-35   # move stage back by the dither radius, plus some distance to account for backlash to overshoot
		self.stage.set_pos = [0,0,zmov_dist]   # prepare move constant list
		self.stage.Move_Stage()		       # move
		self.stage.Read_Encoders()
		self.stage.GUI_Write_Encoder_Values()
                # Exposure time increments in linear steps
                self.time_ent.delete(0,END)
                self.time_ent.insert(0,str(float(increment_value) + float(exptime)))

        else:
            print "No Increment Type found\n"
            self.master.update()
            return
        return

    def StopExposures(self):
        self.stop_exposures = True
        return

    def Define_Frame(self):
        """ Camera control frame, definitions for buttons and labels in the GUI """
        self.frame=Frame(self.master, relief=GROOVE, bd=4)
        self.frame.grid(row=2,column=0,rowspan=2,columnspan=4)
        frame_title = Label(self.frame,text="Camera Control",relief=RAISED,bd=2,width=24, bg="light yellow",font=("Times", 16))
        frame_title.grid(row=0, column=1)

        setup_but = Button(self.frame, text="CCD Setup", width=16,command=self.ccd_setup)
        setup_but.grid(row=0,column=2)
        off_but = Button(self.frame, text="CCD Off", width=16,command=self.ccd_off)
        off_but.grid(row=0,column=3)
        bias_but_on = Button(self.frame, text="BackBias On", width=12,command=self.bbias_on_button)
        bias_but_on.grid(row=1,column=2)
        self.bbias_on_confirm_ent = Entry(self.frame, justify="center", width=12)
        self.bbias_on_confirm_ent.grid(row=2,column=2)
        self.bbias_on_confirm_ent.focus_set()
        bbias_on_confirm_title = Label(self.frame,text="BackBias On Confirm",relief=RAISED,bd=2,width=16)
        bbias_on_confirm_title.grid(row=3, column=2)

        bias_but_off = Button(self.frame, text="Back Bias Off", width=12,command=self.bbias_off)
        bias_but_off.grid(row=1,column=3)

        self.filter = StringVar()
        self.filter.set("r")
        filter_type = OptionMenu(self.frame, self.filter, "u", "g", "r", "i", "z", "y")
        filter_type.grid(row=0, column = 0)
        filter_title = Label(self.frame,text="FILTER",relief=RAISED,bd=2,width=12)
        filter_title.grid(row=1, column=0)

        self.mask_type = StringVar()
        self.mask_type.set("none")
        mask_type = OptionMenu(self.frame, self.mask_type, "none", "40k-spots-30um", "40k-spots-3um", "spot-2um", "spot-5um", "spot-100um", "spot-200um", "target")
        mask_type.grid(row=2, column = 0)
        mask_type_title = Label(self.frame,text="Mask Type",relief=RAISED,bd=2,width=12)
        mask_type_title.grid(row=3, column=0)

        self.sensor_id_ent = Entry(self.frame, justify="center", width=12)
        self.sensor_id_ent.grid(row=4,column=0)
        self.sensor_id_ent.focus_set()
        self.sensor_id_ent.insert(0,self.ccd_sern)
        sensor_id_title = Label(self.frame,text="Sensor_ID",relief=RAISED,bd=2,width=16)
        sensor_id_title.grid(row=5, column=0)

        self.test_type = StringVar()
        self.test_type.set("dark")
        test_type = OptionMenu(self.frame, self.test_type, "dark", "flat", "spot")
        test_type.grid(row=2, column = 1)
        test_type_title = Label(self.frame,text="Test Type",relief=RAISED,bd=2,width=12)
        test_type_title.grid(row=3, column=1)

        self.image_type = StringVar()
        self.image_type.set("dark")
        image_type = OptionMenu(self.frame, self.image_type, "dark", "flat", "bias", "spot")
        image_type.grid(row=4, column = 1)
        image_type_title = Label(self.frame,text="Image Type",relief=RAISED,bd=2,width=12)
        image_type_title.grid(row=5, column=1)

        self.time_ent = Entry(self.frame, justify="center", width=12)
        self.time_ent.grid(row=3,column=3)
        self.time_ent.focus_set()
        self.time_ent.insert(0,'0')
        time_title = Label(self.frame,text="Exposure Time",relief=RAISED,bd=2,width=24)
        time_title.grid(row=4, column=3)

        self.sequence_num_ent = Entry(self.frame, justify="center", width=12)
        self.sequence_num_ent.grid(row=3,column=4)
        self.sequence_num_ent.focus_set()
        self.sequence_num_ent.insert(0,'001')
        sequence_num_title = Label(self.frame,text="Sequence Number",relief=RAISED,bd=2,width=24)
        sequence_num_title.grid(row=4, column=4)

        capture_but = Button(self.frame, text="Expose", width=24,command=self.Expose)
        capture_but.grid(row=0,column=4)

        # Multiple exposure sub frame:
        multi_exp_title = Label(self.frame,text="Multi Exposure Control",relief=RAISED,bd=2,width=24, bg="light yellow",font=("Times", 16))
        multi_exp_title.grid(row=6, column=0)
        self.numinc_ent = Entry(self.frame, justify="center", width=12)
        self.numinc_ent.grid(row=7,column=0)
        self.numinc_ent.focus_set()
        numinc_title = Label(self.frame,text="# of Increments",relief=RAISED,bd=2,width=16)
        numinc_title.grid(row=8, column=0)
        self.numperinc_ent = Entry(self.frame, justify="center", width=12)
        self.numperinc_ent.grid(row=9,column=0)
        self.numperinc_ent.focus_set()
        self.numperinc_ent.insert(0,'1')
        num_per_increment_title = Label(self.frame,text="# Per Increment",relief=RAISED,bd=2,width=16)
        num_per_increment_title.grid(row=10, column=0)
        self.start_sequence_num_ent = Entry(self.frame, justify="center", width=12)
        self.start_sequence_num_ent.grid(row=7,column=1)
        self.start_sequence_num_ent.focus_set()
        self.start_sequence_num_ent.insert(0,'001')
        start_sequence_num_title = Label(self.frame,text="Starting Seq Num",relief=RAISED,bd=2,width=16)
        start_sequence_num_title.grid(row=8, column=1)
        self.dither_radius_ent = Entry(self.frame, justify="center", width=12)
        self.dither_radius_ent.grid(row=9,column=1)
        self.dither_radius_ent.focus_set()
        self.dither_radius_ent.insert(0,'0')
        dither_radius_title = Label(self.frame,text="Dither Radius (steps)",relief=RAISED,bd=2,width=24)
        dither_radius_title.grid(row=10, column=1)
        self.increment_type = StringVar()
        self.increment_type.set("None")
        self.increment_type = StringVar()
        self.increment_type.set("")
        increment_type = OptionMenu(self.frame, self.increment_type, "None", "X", "Y", "Z", "Exp(Log)", "Exp(Linear)", "V-curve (Linear)", "Light Intensity", "Cooling Curve")
        increment_type.grid(row=7, column = 2)
        increment_type_title = Label(self.frame,text="Increment Type",relief=RAISED,bd=2,width=12)
        increment_type_title.grid(row=8, column=2)
        self.increment_value_ent = Entry(self.frame, justify="center", width=12)
        self.increment_value_ent.grid(row=7,column=3)
        self.increment_value_ent.focus_set()
        self.increment_value_ent.insert(0,'0')
        increment_value_title = Label(self.frame,text="Increment",relief=RAISED,bd=2,width=12)
        increment_value_title.grid(row=8, column=3)
        stop_exposures_but = Button(self.frame, text="Stop Exposures", width=16,command=self.StopExposures)
        stop_exposures_but.grid(row=10,column=3)
        multi_capture_but = Button(self.frame, text="Start Exposures\nNumber of Exposures = \n # of Increments * # Per Increment", width=26,command=self.MultiExpose)
        multi_capture_but.grid(row=7,column=4)
        self.delay_ent = Entry(self.frame, justify="center", width=12)
        self.delay_ent.grid(row=9,column=4)
        self.delay_ent.focus_set()
        self.delay_ent.insert(0,'0')
        delay_title = Label(self.frame,text="Delay Before Start(sec)",relief=RAISED,bd=2,width=26)
        delay_title.grid(row=10, column=4)

	return


    def runcmd(self, args,env=None,verbose=0):
        # runcmd is used to make external calls, where args is a list of what would be space separated arguments,
        # with the convention that args[0] is the name of the command.
        # An argument of space separated names should not be quoted
        # Otherwise, this command receives stdout and stderr back through a pipe and returns it.
        # On error, this program will throw 
        # StandardError with a string containing the stderr return from the calling program.
        # Throws may also occur directly from 
        # process.POpen (e.g., OSError. This program will also return a cmd style
        # facsimile of  the command and arguments. 
        cmdstring = args[0]
        for i in range(1,len(args)):
            if args[i].find(' ') >= 0: cmdstring += " '%s'" % args[i]
            else: cmdstring += " %s" % args[i]

        errcode = 0
        #print "In runcmd.  Running the following command:%s \n"%cmdstring

        # Call the requested command, wait for its return, 
        # then get any return pipe output
        proc = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=False,env=env) 

        errcode = proc.wait()
        (stdoutdata, stderrdata) = proc.communicate()
        if stdoutdata.find(' ') >= 0: 
            sys.stdout.write(stdoutdata)
        if stderrdata.find(' ') >= 0: 
            sys.stderr.write(stderrdata)
        # The calling program will not throw on failure, 
        # but we should to make it compatible with
        # Python programming practices
        if errcode:
            errstring = 'Command "%s" failed with code %d\n------\n%s\n' % (cmdstring,errcode,stderrdata) 
            raise StandardError(errstring)

        return (stdoutdata, stderrdata)

    def bbias_on(self):
        print('Connecting to BSS controller...')
        self.bk.Set_Voltage(-self.vbb)
        self.bk.bbias_on()
        time.sleep(0.5)
        if self.bss_relay_status:
            self.relay.openPhidget(403840) # Serial number 403840 is the Vbb control Phidgets relay
            self.relay.waitForAttach(10000)
            if (self.relay.isAttached() and self.relay.getSerialNum() == 403840):
                self.relay.setOutputState(0,True)
                print('BSS is now ON')
                print('Done!')
                self.master.update()
                self.relay.closePhidget()
                return
            else : 
                print('Failed to connect to Phidget controller') 
                self.master.update()
                self.relay.closePhidget()
                return
        else : 
            print('Failed to connect to Phidget controller') 
            self.master.update()
            self.relay.closePhidget()
            return

    def bbias_on_button(self):
        # This is called when bbias_on is called from the GUI.
        # It requires confirmation so as not to damage the device.
        if self.bbias_on_confirm_ent.get() != 'Y':
            print "The device can be damaged if backbias is connected before power up."
            print "Make certain that you have run ccd_setup before bbias_on."
            print "If you are certain, enter 'Y' in the confirm box"
            print "Not connecting bbias. BSS is still off.\n"
            self.master.update()
            self.bbias_on_confirm_ent.delete(0,END)
            self.bbias_on_confirm_ent.insert(0,'')
            return
        else:
            self.bbias_on()
            self.bbias_on_confirm_ent.delete(0,END)
            self.bbias_on_confirm_ent.insert(0,'')
            return

    def bbias_off(self):
        """Python version of the bbias_off script"""
        print('Connecting to BSS controller...')
        # First set the voltage off at the BK and turn the output off
        self.bk.Set_Voltage(0.0)
        self.bk.bbias_off()
        time.sleep(0.5)
        if self.bss_relay_status:
            self.relay.openPhidget(403840) # Serial number 403840 is the Vbb control Phidgets relay
            self.relay.waitForAttach(10000)
            if (self.relay.isAttached() and self.relay.getSerialNum() == 403840):
                self.relay.setOutputState(0,False)
                print('BSS is now OFF')
                print('Done!')
                self.relay.closePhidget()
                return
            else : 
                sys.exit('Failed to connect to Phidget controller') 
                self.relay.closePhidget()
                return
        else : 
            print('Failed to connect to Phidget controller') 
            self.relay.closePhidget()
            return

    def exp_acq(self, exptime=0.0, fits_header_data=None, clears=1, annotation=None, locations=None):
        """CCS exposure commands"""

	fp.setHeaderKeywords(fits_header_data)
        imageName = fp.allocateImageName()
        fp.clearAndStartNamedIntegration(imageName, clears, annotation, locations)
        time.sleep(CLEARDELAY)
        self.shutter.openShutter(exptime)
        fp.endIntegration()
        fp.waitForFitsFiles(imageTimeout)

        return

    def dark_acq(self, exptime=0.0, fits_header_data=None, clears=1, annotation=None, locations=None):

	fp.setHeaderKeywords(fits_header_data)
        imageName = fp.allocateImageName()
        fp.clearAndStartNamedIntegration(imageName, clears, annotation, locations)
        time.sleep(CLEARDELAY)
        time.sleep(exptime)
        fp.endIntegration()
        fp.waitForFitsFiles(imageTimeout)

        return

    def ccd_setup(self):
        raise NotImplementedError

    def ccd_off(self):
        raise NotImplementedError

    def gain(self, value):
        """Python version of the CamCmds gain script"""
        if value == "LOW":
            self.runcmd([self.edtsaodir+"/edtwriten", "-c", "50200000"])
            print 'Setting gain to LOW.\n'
        elif value == "HIGH":
            self.runcmd([self.edtsaodir+"/edtwriten", "-c", "50300000"])
            print 'Setting gain to HIGH.\n'
        else:
            print "Bogus gain setting\n"
            print 'Usage: gain("LOW") or gain("HIGH")\n'
        self.master.update()
        return
