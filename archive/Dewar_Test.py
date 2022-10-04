#!/usr/bin/env python
import sys
import time, datetime
sys.path.append('/sandbox/lsst/lsst/GUI')
import DewarFill

#************** START OF MAIN PROGRAM ****************** 
dewarfill = DewarFill.DewarFill('dummy')

starttime = time.time()
elapsed = 0.0
dewarfill.StartFill()

file = open('temp_test.dat','w')

while elapsed < 150.0:
    temp = dewarfill.MeasureOverFlowTemp()
    line = "Temp at %s is %f\n"%(datetime.datetime.now(),temp)
    file.write(line)
    elapsed = time.time() - starttime
    time.sleep(0.25)
file.close()
dewarfill.StopFill()
#************** END OF MAIN PROGRAM ****************** 
