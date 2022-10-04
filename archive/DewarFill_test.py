#!/usr/bin/env python
import sys
import time, datetime
sys.path.append('/sandbox/lsst/lsst/GUI')
import DewarFill

#************** START OF MAIN PROGRAM ****************** 
dewarfill = DewarFill.DewarFill('dummy')

dewarfill.StartFill()
dewarfill.StopFill()
#************** END OF MAIN PROGRAM ****************** 
