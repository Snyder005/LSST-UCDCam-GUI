#!/usr/bin/env python
#Authors: Andrew Bradshaw, Perry Gee, Craig Lage, UC Davis; 
#Date: 12-May-15
# This is the latest GUI for controlling
# the LSST Simulator

from Tkinter import *
import sys
import StdOut_StdErr
import Stage
import Sphere
import Camera
import Comm_Status
import Analysis
import Lakeshore_335
import BK_Precision_9184
import DewarFill

#************** START OF MAIN PROGRAM ****************** 
master = Tk() # Main GUI Window
master.title("Simulator Control UI")
stage = Stage.Stage(master)
lakeshore = Lakeshore_335.Lakeshore(master)
sphere = Sphere.Sphere(master)
bk = BK_Precision_9184.BK_Precision_9184(master)
camera = Camera.Camera(master,stage, sphere, lakeshore, bk)
dewarfill = DewarFill.DewarFill(master)
comm_status = Comm_Status.Comm_Status(master,stage, sphere, camera, lakeshore, bk, dewarfill)
analysis = Analysis.Analysis(master,camera)
stdout_stderr = StdOut_StdErr.StdOut_StdErr(master)

stage.Define_Frame()
sphere.Define_Frame()
camera.Define_Frame()
dewarfill.Define_Frame()
analysis.Define_Frame()
stdout_stderr.Define_Frame()
comm_status.Define_Frame()
master.mainloop() 

# Return stdout and stderr to terminal window
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
print "Shutting Down\n"

try:
    sphere.Final_Light_Off()
    camera.ccd_off()
    comm_status.Close_All()
except Exception as e:
    print "Failure in LSST_GUI shutdown. Exception of type %s and args = \n"%type(e).__name__, e.args    
    sys.stdout.flush()
try:
    print "Closing ds9\n"
    analysis.d.set('exit')
except Exception as e:
    print "Failure ds9 shutdown. Exception of type %s and args = \n"%type(e).__name__, e.args    
    sys.stdout.flush()
#************** END OF MAIN PROGRAM ****************** 
