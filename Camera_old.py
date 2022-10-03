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

class Camera(object):
    def __init__(self, master, stage, sphere, lakeshore):
        self.master = master
        self.stage = stage
        self.sphere = sphere
        self.lakeshore = lakeshore

        CfgFile = "/sandbox/lsst/lsst/GUI/UCDavis.cfg"
        if self.CheckIfFileExists(CfgFile):
            self.CfgFile = CfgFile
        else:
            print "Configuration file %s not found. Exiting.\n"%CfgFile
            sys.exit()
            return
        self.edtsaodir = eolib.getCfgVal(self.CfgFile,"EDTSAO_DIR")
        self.EDTdir = eolib.getCfgVal(self.CfgFile,"EDT_DIR")
        self.fitsfilename = "dummy.fits" # Just a dummy - not really used
        self.relay = InterfaceKit()
        return
            
    def GetVoltageLookup(self):
        try:
            self.voltage_lookup = [  # Lookup table with voltage values
                {"Name":"VCLK_LO",    "Value": float(eolib.getCfgVal(self.CfgFile,"VCLK_LO")),    "Vmin":  0.0, "Vmax": 10.0, "chan":["a0188"]},
                {"Name":"VCLK_HI",    "Value": float(eolib.getCfgVal(self.CfgFile,"VCLK_HI")),    "Vmin":  0.0, "Vmax": 10.0, "chan":["a0080"]},
                {"Name":"VV4",        "Value": float(eolib.getCfgVal(self.CfgFile,"VV4")),        "Vmin":-10.0, "Vmax":  0.0, "chan":["a0280"]},
                {"Name":"VDD",        "Value": float(eolib.getCfgVal(self.CfgFile,"VDD")),        "Vmin":  0.0, "Vmax": 30.0, "chan":["a0380"]},
                {"Name":"VRD",        "Value": float(eolib.getCfgVal(self.CfgFile,"VRD")),        "Vmin":  0.0, "Vmax": 20.0, "chan":["a0384"]},
                {"Name":"VOD",        "Value": float(eolib.getCfgVal(self.CfgFile,"VOD")),        "Vmin":  0.0, "Vmax": 30.0, "chan":["a0388","a038c"]},
                {"Name":"VOG",        "Value": float(eolib.getCfgVal(self.CfgFile,"VOG")),        "Vmin": -5.0, "Vmax":  0.0, "chan":["a0288","a028c"]},
                {"Name":"PAR_CLK_LO", "Value": float(eolib.getCfgVal(self.CfgFile,"PAR_CLK_LO")), "Vmin":-10.0, "Vmax":  0.0, "chan":["a0184"]},
                {"Name":"PAR_CLK_HI", "Value": float(eolib.getCfgVal(self.CfgFile,"PAR_CLK_HI")), "Vmin":  0.0, "Vmax": 10.0, "chan":["a0084"]},
                {"Name":"SER_CLK_LO", "Value": float(eolib.getCfgVal(self.CfgFile,"SER_CLK_LO")), "Vmin":-10.0, "Vmax":  0.0, "chan":["a0180"]},
                {"Name":"SER_CLK_HI", "Value": float(eolib.getCfgVal(self.CfgFile,"SER_CLK_HI")), "Vmin":  0.0, "Vmax": 10.0, "chan":["a008c"]},
                {"Name":"RG_LO",      "Value": float(eolib.getCfgVal(self.CfgFile,"RG_LO")),      "Vmin":-10.0, "Vmax":  0.0, "chan":["a018c"]},
                {"Name":"RG_HI",      "Value": float(eolib.getCfgVal(self.CfgFile,"RG_HI")),      "Vmin":  0.0, "Vmax": 10.0, "chan":["a0088"]}]
        except:
            print "Voltage lookup routine failed!"
        return

    def GetOffsetLookup(self):
        try:
            self.offset_lookup = [ # Lookup table with channel offsets
                {"Segment":1,  "Channel":1,  "chan":"3008", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_1"))},
                {"Segment":2,  "Channel":5,  "chan":"3108", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_2"))},
                {"Segment":3,  "Channel":2,  "chan":"3018", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_3"))},
                {"Segment":4,  "Channel":6,  "chan":"3118", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_4"))},
                {"Segment":5,  "Channel":3,  "chan":"3028", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_5"))},
                {"Segment":6,  "Channel":7,  "chan":"3128", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_6"))},
                {"Segment":7,  "Channel":4,  "chan":"3038", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_7"))},
                {"Segment":8,  "Channel":8,  "chan":"3138", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_8"))},
                {"Segment":9,  "Channel":9,  "chan":"3208", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_9"))},
                {"Segment":10, "Channel":13, "chan":"3308", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_10"))},
                {"Segment":11, "Channel":10, "chan":"3218", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_11"))},
                {"Segment":12, "Channel":14, "chan":"3318", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_12"))},
                {"Segment":13, "Channel":11, "chan":"3228", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_13"))},
                {"Segment":14, "Channel":15, "chan":"3328", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_14"))},
                {"Segment":15, "Channel":12, "chan":"3238", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_15"))},
                {"Segment":16, "Channel":16, "chan":"3338", "offset":int(eolib.getCfgVal(self.CfgFile,"OFF_SEG_16"))}]
        except:
            print "Segment Offset lookup routine failed!"
        return

    def CheckIfFileExists(self, filename):
        try:
            FileSize = os.path.getsize(filename)
            return True
        except OSError:
            return False

    def Initialize_BSS_Relay(self):
        print('Connecting to BSS controller...')
        self.relay.openPhidget()
        self.relay.waitForAttach(10000)
        if (self.relay.isAttached()):
            print "Successfully initialized BSS Relay\n" 
            self.bss_relay_status = True
        else:
            print "Failed to initialize BSS relay\n"
            self.bss_relay_status = False
        self.relay.closePhidget()
        self.master.update()
        return
        
    def Close_BSS_Relay(self):
        print('Closing BSS relay connection...')
        self.relay.closePhidget()
        self.master.update()
        return

    def Check_Communications(self):
        """Checks on communications staus with the camera, called by the communications frame/class"""
        self.comm_status = False
        (stdoutdata, stderrdata) = self.runcmd([self.edtsaodir+"/fclr"])
        if stdoutdata.split()[1] == 'done' and stderrdata == '':
            self.comm_status = True
        self.bss_relay_status = False
        self.relay.openPhidget()
        self.relay.waitForAttach(10000)
        if (self.relay.isAttached()):
            self.bss_relay_status = True
        self.relay.closePhidget()
        self.master.update()
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
        sequence_num = self.sequence_num_ent.get()
        filter=self.filter.get()
        self.fitsfilename = ("testdata/"+sensor_id+"_"+test_type+"_"+image_type+"_%03d_"+timestamp+".fits")%(int(sequence_num))
        print "Filename:%s\n"%self.fitsfilename
        sys.stdout.flush()
        self.master.update()
        if image_type == 'light':
            self.exp_acq(exptime=exptime, fitsfilename=self.fitsfilename)
        elif image_type == 'dark':
            self.dark_acq(exptime=exptime, fitsfilename=self.fitsfilename)
        elif image_type == 'bias':
            # A bias exposure is just a dark exposure with 0 time.
            self.dark_acq(exptime=0.0, fitsfilename=self.fitsfilename)
        else:
            print "Image type not recogized.  Exposure not done."
            self.master.update()
            return
        try:
            self.sphere.Read_Photodiode()
            mondiode = self.sphere.diode_current
            srcpwr = self.sphere.light_intensity
            self.lakeshore.Read_Temp()
            self.master.update()
            self.stage.Read_Encoders()
            # Add other things here(temp, etc. when they are available)
            ucdavis2lsst.fix(self.fitsfilename, self.CfgFile, sensor_id, test_type, image_type, sequence_num, exptime, filter, srcpwr, mondiode, \
                             self.lakeshore.Temp_A, self.lakeshore.Temp_B, self.lakeshore.Temp_Set, stage_pos = self.stage.read_pos)
        except:
            print "Fits file correction failed. File %s is not LSST compliant"%self.fitsfilename
            self.master.update()
        return

    def MultiExpose(self):
        #Launches a series of exposures
        numexp = int(self.numexp_ent.get())
        start_sequence_num = int(self.start_sequence_num_ent.get())
        increment_type = self.increment_type.get()
        increment_value = self.increment_value_ent.get()
        print "Multiple Exposures started. Numexp = %d, StartNum = %d, type = %s, value = %s"%(numexp,start_sequence_num,increment_type, increment_value)
        for exposure_counter in range(numexp):
            seq_num = start_sequence_num + exposure_counter
            self.sequence_num_ent.delete(0,END)
            self.sequence_num_ent.insert(0,"%03d"%seq_num)
            if increment_type == "None":
                self.Expose()
            elif increment_type == "X":
                if exposure_counter != 0:
                    self.stage.set_pos = [int(increment_value), 0, 0]
                    self.stage.Move_Stage()
                    self.stage.Read_Encoders()
                    self.stage.GUI_Write_Encoder_Values()
                    self.master.update()
                self.Expose()
            elif increment_type == "Y":
                if exposure_counter != 0:
                    self.stage.set_pos = [0, int(increment_value), 0]
                    self.stage.Move_Stage()
                self.stage.Read_Encoders()
                self.stage.GUI_Write_Encoder_Values()
                self.master.update()
                self.Expose()
            elif increment_type == "Z":
                if exposure_counter != 0:
                    self.stage.set_pos = [0, 0, int(increment_value)]
                    self.stage.Move_Stage()
                self.stage.Read_Encoders()
                self.stage.GUI_Write_Encoder_Values()
                self.master.update()
                self.Expose()
            elif increment_type == "Exp":
                exptime = self.time_ent.get()
                self.Expose()
                # Exposure time increments in log steps, not linear
                self.time_ent.delete(0,END)
                self.time_ent.insert(0,str(float(increment_value) * float(exptime)))
            else:
                print "No Increment Type found\n"
                return
        return

    def Define_Frame(self):
        """ Camera control frame, definitions for buttons and labels in the GUI """
        self.frame=Frame(self.master, relief=GROOVE, bd=4)
        self.frame.grid(row=1,column=0)
        frame_title = Label(self.frame,text="Camera Control",relief=RAISED,bd=2,width=24, bg="light yellow",font=("Times", 16))
        frame_title.grid(row=0, column=1)

        setup_but = Button(self.frame, text="STA 3800 Setup", width=16,command=lambda:self.sta3800_setup())
        setup_but.grid(row=0,column=2)
        off_but = Button(self.frame, text="STA 3800 Off", width=16,command=lambda:self.sta3800_off())
        off_but.grid(row=0,column=3)
        bias_but_on = Button(self.frame, text="BackBias On", width=12,command=lambda:self.bbias_on_button())
        bias_but_on.grid(row=1,column=2)
        self.bbias_on_confirm_ent = Entry(self.frame, justify="center", width=12)
        self.bbias_on_confirm_ent.grid(row=2,column=2)
        self.bbias_on_confirm_ent.focus_set()
        bbias_on_confirm_title = Label(self.frame,text="BackBias On Confirm",relief=RAISED,bd=2,width=16)
        bbias_on_confirm_title.grid(row=3, column=2)

        bias_but_off = Button(self.frame, text="Back Bias Off", width=12,command=lambda:self.bbias_off())
        bias_but_off.grid(row=1,column=3)

        self.filter = StringVar()
        self.filter.set("R")
        filter_type = OptionMenu(self.frame, self.filter, "U", "G", "R", "I", "Z", "Y")
        filter_type.grid(row=0, column = 0)
        filter_title = Label(self.frame,text="FILTER",relief=RAISED,bd=2,width=12)
        filter_title.grid(row=1, column=0)

        self.sensor_id_ent = Entry(self.frame, justify="center", width=12)
        self.sensor_id_ent.grid(row=3,column=0)
        self.sensor_id_ent.focus_set()
        self.sensor_id_ent.insert(0,'112-06')
        sensor_id_title = Label(self.frame,text="Sensor_ID",relief=RAISED,bd=2,width=16)
        sensor_id_title.grid(row=4, column=0)

        self.test_type = StringVar()
        self.test_type.set("dark")
        test_type = OptionMenu(self.frame, self.test_type, "dark", "flat", "spot-30um", "spot-3um", "target")
        test_type.grid(row=2, column = 1)
        test_type_title = Label(self.frame,text="Test Type",relief=RAISED,bd=2,width=12)
        test_type_title.grid(row=3, column=1)

        self.image_type = StringVar()
        self.image_type.set("dark")
        image_type = OptionMenu(self.frame, self.image_type, "dark", "bias", "light")
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

        capture_but = Button(self.frame, text="Expose", width=24,command=lambda:self.Expose())
        capture_but.grid(row=0,column=4)

        # Multiple exposure sub frame:
        multi_exp_title = Label(self.frame,text="Multi Exposure Control",relief=RAISED,bd=2,width=24, bg="light yellow",font=("Times", 16))
        multi_exp_title.grid(row=6, column=0)
        self.numexp_ent = Entry(self.frame, justify="center", width=12)
        self.numexp_ent.grid(row=7,column=0)
        self.numexp_ent.focus_set()
        numexp_title = Label(self.frame,text="# of Exposures",relief=RAISED,bd=2,width=24)
        numexp_title.grid(row=8, column=0)
        self.start_sequence_num_ent = Entry(self.frame, justify="center", width=12)
        self.start_sequence_num_ent.grid(row=7,column=1)
        self.start_sequence_num_ent.focus_set()
        self.start_sequence_num_ent.insert(0,'001')
        start_sequence_num_title = Label(self.frame,text="Starting Seq. Num.",relief=RAISED,bd=2,width=24)
        start_sequence_num_title.grid(row=8, column=1)
        self.increment_type = StringVar()
        self.increment_type.set("None")
        increment_type = OptionMenu(self.frame, self.increment_type, "None", "X", "Y", "Z", "Exp")
        increment_type.grid(row=7, column = 2)
        increment_type_title = Label(self.frame,text="Increment Type",relief=RAISED,bd=2,width=12)
        increment_type_title.grid(row=8, column=2)
        self.increment_value_ent = Entry(self.frame, justify="center", width=12)
        self.increment_value_ent.grid(row=7,column=3)
        self.increment_value_ent.focus_set()
        self.increment_value_ent.insert(0,'0')
        increment_value_title = Label(self.frame,text="Increment",relief=RAISED,bd=2,width=24)
        increment_value_title.grid(row=8, column=3)
        multi_capture_but = Button(self.frame, text="Start Exposures", width=24,command=lambda:self.MultiExpose())
        multi_capture_but.grid(row=7,column=4)

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
        """Python version of the bbias_on script"""
        print('Connecting to BSS controller...')
        if self.bss_relay_status:
            self.relay.openPhidget()
            self.relay.waitForAttach(10000)
            if (self.relay.isAttached()) : 
                self.relay.setOutputState(0,True)
                print('BSS is now ON')
                print('Done!')
                self.relay.closePhidget()
                return
            else : 
                print('Failed to connect to Phidget controller') 
                self.relay.closePhidget()
                return
        else : 
            print('Failed to connect to Phidget controller') 
            return

    def bbias_on_button(self):
        # This is called when bbias_on is called from the GUI.
        # It requires confirmation so as not to damage the device.
        if self.bbias_on_confirm_ent.get() != 'Y':
            print "The device can be damaged if backbias is connected before power up."
            print "Make certain that you have run sta3800_setup before bbias_on."
            print "If you are certain, enter 'Y' in the confirm box"
            print "Not connecting bbias. BSS is still off.\n"
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
        if self.bss_relay_status:
            self.relay.openPhidget()
            self.relay.waitForAttach(10000)
            if (self.relay.isAttached()) : 
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
            return

    def sixteen_ch_setup(self):
        """Python version of the CamCmd 16ch_setup script"""

        print "Setting up for generic 16 channel readout...\n"
        # initialize edt interface
        InitFile = eolib.getCfgVal(self.CfgFile,"INIT_FILE")
        if not self.CheckIfFileExists(InitFile):
            print "Init File not found.  Exiting sixteen channel setup"
            return
        #self.runcmd(["initrcx0"]) # This script just does the following:
        self.runcmd([self.EDTdir+"/initcam", "-u", "0", "-c", "0", "-f", InitFile]) 

        self.runcmd([self.edtsaodir+"/crst"]) # Camera reset
        # Turn off the greyscale generator
        print "Turning greyscale generator off\n"
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "30400000"]) # ad board #1 gray scale off
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "31400000"]) # ad board #2 gray scale off
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "32400000"]) # ad board #3 gray scale off
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "33400000"]) # ad board #4 gray scale off

        # Set the system gain to high
        self.gain("HIGH")

        # Set unidirectional mode
        print "Setting unidirectional CCD serial shift mode\n"
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "43000001"]) # uni on

        # Set split mode on. "Why on?" you ask. Beats me.
        print "Setting CCD serial register shifts to split mode\n"
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "41000001"]) # split on   

        self.sta3800_channels()

        print "Setting default ADC offsets\n"

        self.sta3800_offsets()
        self.Check_Communications()
        print "16ch_setup Done.\n"
        self.master.update()
        return

    def exp_acq(self, exptime=0.0, fitsfilename='test.fits'):
        """Python version of the CamCmd exp_acq script"""
        NoFlushFile = eolib.getCfgVal(self.CfgFile,"EXP_NO_FLUSH_FILE")
        if not self.CheckIfFileExists(NoFlushFile):
            print "No Flush File not found.  Exiting exp_acq"
            return
        FlushFile = eolib.getCfgVal(self.CfgFile,"EXP_FLUSH_FILE")
        if not self.CheckIfFileExists(FlushFile):
            print "Flush File not found.  Exiting exp_acq"
            return
        self.runcmd([self.edtsaodir+"/fclr", "2"])                       # clear the CCD 
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "50000080"])     # setup for tens of millisecond exposure time
        self.runcmd([self.edtsaodir+"/edtwriteblk", "-f", NoFlushFile])     # load the signal file to stop parallel flushing
        self.runcmd([self.edtsaodir+"/expose", str(exptime)])            # do the exposure
        self.runcmd([self.edtsaodir+"/image16", "-F", "-f", fitsfilename, "-x", "542", "-y", "2022", "-n", "16"]) # readout
        self.runcmd([self.edtsaodir+"/edtwriteblk", "-f", FlushFile])       # load the signal file to re-start parallel flushing
        return

    def dark_acq(self, exptime=0.0, fitsfilename='test.fits'):
        """Python version of the CamCmd dark_acq script"""
        NoFlushFile = eolib.getCfgVal(self.CfgFile,"DARK_NO_FLUSH_FILE")
        if not self.CheckIfFileExists(NoFlushFile):
            print "No Flush File not found.  Exiting dark_acq"
            return
        FlushFile = eolib.getCfgVal(self.CfgFile,"DARK_FLUSH_FILE")
        if not self.CheckIfFileExists(FlushFile):
            print "Flush File not found.  Exiting dark_acq"
            return
        self.runcmd([self.edtsaodir+"/fclr", "2"])                       # clear the CCD 
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "50000080"])     # setup for tens of millisecond exposure time
        self.runcmd([self.edtsaodir+"/edtwriteblk", "-f", NoFlushFile])     # load the signal file to stop parallel flushing
        self.runcmd([self.edtsaodir+"/dark", str(exptime)])            # do the exposure
        self.runcmd([self.edtsaodir+"/image16", "-F", "-f", fitsfilename, "-x", "542", "-y", "2022", "-n", "16"]) # readout
        self.runcmd([self.edtsaodir+"/edtwriteblk", "-f", FlushFile])       # load the signal file to re-start parallel flushing
        return

    def sta3800_setup(self):
        """Python version of the sta3800_setup script"""
        self.sixteen_ch_setup()
        print "Setting up STA3800 ...\n"
        self.sta3800_timing()
        self.sta3800_channels()
        self.sta3800_volts()
        self.sta3800_offsets()
        self.gain("LOW")
        print "sta3800_setup done.\n"
        self.master.update()
        return

    def sta3800_off(self):
        """Python version of the sta3800_off script"""
        print"Powering down the sta3800 device...\n"
        self.GetVoltageLookup()
        self.bbias_off()
        time.sleep(0.5)
        supplies = self.voltage_lookup
        supplies.reverse()
        # Powering down in reverse order of power up
        for supply in supplies:
            name = supply["Name"]
            vmin = supply["Vmin"]
            vmax = supply["Vmax"]
            value = 0.0

            if value < vmin or value > vmax:
                print "Requested voltage for %s exceeds limits.  Exiting voltage setup\n"%name
                return
            if vmin < 0.0:
                DACval = int(round(4095 - round(round((value - vmin) / (vmax - vmin), 3) * 4095, 3), 0))
            else:
                DACval = int(round(round((value - vmin) / (vmax - vmin), 3) * 4095, 0))
            for chan in supply["chan"]:
                print "Command= %s"%(self.edtsaodir+"/edtwriten -c %s%03x"%(chan,DACval))
                self.runcmd([self.edtsaodir+"/edtwriten", "-c", "%s%03x"%(chan,DACval)])
                #print "Set Voltage %s to %.2f volts: at ADC channel %s DAC setting %03x"%(name,value,chan,DACval)
                print "Set Voltage %s to %.2f volts"%(name,value)
            time.sleep(0.1)
        print "sta3800_off done.\n"
        self.master.update()
        return

    def gain(self, value):
        """Python version of the CamCmds gain script"""
        if value == "LOW":
            self.runcmd([self.edtsaodir+"/edtwriten", "-c", "50200000"])
        elif value == "HIGH":
            self.runcmd([self.edtsaodir+"/edtwriten", "-c", "50300000"])
        else:
            print "Bogus gain setting\n"
            print 'Usage: gain("LOW") or gain("HIGH")\n'
        return

    def sta3800_timing(self):
        """Python version of the sta3800_timing script"""
        print "Setting up STA3800 default timing...\n"
        Par_Clk_Delay = int(eolib.getCfgVal(self.CfgFile,"PAR_CLK_DELAY"))
        print "Setting parallel clock delay to %d\n"%Par_Clk_Delay
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "46000%03x"%Par_Clk_Delay]) # Set parallel clock delay to 6

        SigBFile = eolib.getCfgVal(self.CfgFile,"TIM_FILE")
        if not self.CheckIfFileExists(SigBFile):
            print "Signal file not found.  May need to run Perl conversion routine. Exiting sta3800_timing"
            return
        print "Loading serial readout signal file %s\n"%SigBFile
        self.runcmd([self.edtsaodir+"/edtwriteblk", "-f", SigBFile])     # load the signal file

        PatBFile = eolib.getCfgVal(self.CfgFile,"PAT_FILE")
        if not self.CheckIfFileExists(PatBFile):
            print "Pattern file not found.  May need to run Perl conversion routine. Exiting sta3800_timing"
            return
        print "Loading default pattern file %s\n"%PatBFile
        self.runcmd([self.edtsaodir+"/edtwriteblk", "-f", PatBFile])     # load the pattern file
        print "sta3800_timing done.\n"
        self.master.update()
        return

    def sta3800_offsets(self):
        """Python version of the sta3800_offsets script"""

        self.GetOffsetLookup()         
        for segment in self.offset_lookup:
            seg = segment["Segment"]
            chan = segment["chan"]
            channel = segment["Channel"]
            offset = segment["offset"]
            self.runcmd([self.edtsaodir+"/edtwriten", "-c", "%s0%03x"%(chan,offset)])
            print "Set segment %2d offset to %4d"%(seg,offset)

        print "sta3800_offsets done.\n"
        self.master.update()
        return

    def sta3800_volts(self):
        """Python version of the sta3800_volts script"""
        print "Setting up sta3800 default voltages...\n"
        self.GetVoltageLookup()
        self.bbias_off()
        time.sleep(0.5)
        supplies = self.voltage_lookup
        for supply in supplies:
            name = supply["Name"]
            vmin = supply["Vmin"]
            vmax = supply["Vmax"]
            value = supply["Value"]

            if value < vmin or value > vmax:
                print "Requested voltage for %s exceeds limits.  Exiting voltage setup\n"%name
                return
            if vmin < 0.0:
                DACval = int(round(4095 - round(round((value - vmin) / (vmax - vmin), 3) * 4095, 3), 0))
            else:
                DACval = int(round(round((value - vmin) / (vmax - vmin), 3) * 4095, 0))
            for chan in supply["chan"]:
                print "Command= %s"%(self.edtsaodir+"/edtwriten -c %s%03x"%(chan,DACval))
                self.runcmd([self.edtsaodir+"/edtwriten", "-c", "%s%03x"%(chan,DACval)])
                #print "Set Voltage %s to %.2f volts: at ADC channel %s DAC setting %03x"%(name,value,chan,DACval)
                print "Set Voltage %s to %.2f volts"%(name,value)
            time.sleep(0.1)
        self.bbias_on()
        print "sta3800_volts done.\n"
        self.master.update()
        return

    def sta3800_channels(self):
        """Python version of the sta3800_channels script"""

        print "Setting up for 16 channel readout...\n"

        # We want them in order, and we want all of them
        print "Set up channel readout order to 0,1,2,3...15\n"
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000042"]) #  Board 0
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000140"]) # 
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000243"]) #  
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000341"])  #
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000446"]) #  Board 1
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000544"]) # 
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000647"]) #  
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000745"])  #
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000848"]) #  Board 2
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "5100094f"]) # 
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000a4c"]) #  
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000b4e"])  #
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000c49"]) #  Board 3
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000d4b"]) # 
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51000e4d"]) #  
        self.runcmd([self.edtsaodir+"/edtwriten", "-c", "51008f4a"])  #

        print "sta3800_channels done.\n"
        self.master.update()
        return
