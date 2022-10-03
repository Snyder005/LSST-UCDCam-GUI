
#!/usr/bin/env python
#Author: Craig Lage, Andrew Bradshaw, Perry Gee, UC Davis; 
#Date: 17-Feb-15
# These files contains various subroutines
# needed to run the LSST Simulator
# This class interfaces to the Dylos 1100 Pro Particle Counter.
import os, sys
import ew, time
if os.path.isfile('send_warning'):
     mtime = os.path.getmtime('send_warning')
else:
     mtime = 0

wfile=open('send_warning', 'w')
wfile.write("this is a test warning")
wfile.close()

if os.path.isfile('send_warning'):
    new_mtime = os.path.getmtime('send_warning')
    if new_mtime > mtime:
         print "new warning file found"
         r_file = open('send_warning', 'r')
         lines = r_file.readlines()      
         print "Dylos Warning at "+time.ctime(new_mtime)
         ew.Send_Warning("Dylos Warning at "+time.ctime(new_mtime), lines[0])
