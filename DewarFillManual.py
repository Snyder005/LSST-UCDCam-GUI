#!/usr/bin/env python
import sys
import time, datetime
sys.path.append('/sandbox/lsst/lsst/GUI')
import DewarFill

#************** START OF MAIN PROGRAM ****************** 
dewarfill = DewarFill.DewarFill('dummy')
fill_time = int(sys.argv[1])
print "Filling for %d seconds"%fill_time
dewarfill.StartFill()
time.sleep(fill_time)
dewarfill.StopFill()
dewarfill.LogFill()
print "Done"
#************** END OF MAIN PROGRAM ****************** 
