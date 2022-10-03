#!/usr/bin/env python
#Author: Craig Lage, UC Davis; 
#Date: 18-Nov-14
# These files contains various subroutines
# needed to run the LSST Simulator
# This class sets the Tkinter frame for the output of routines and print statements, as well as error messages

# Using the Tkinter module for interface design
from Tkinter import *
import sys

class StdOut_StdErr(object):
    def __init__(self, master):
        self.master = master
        return

    def Define_Frame(self):
        ## Std_Out frame
        self.frame=Frame(self.master, bd=4)
        self.frame.grid(row=4,column=0,rowspan=6,columnspan=4)
        stdout_title = Label(self.frame,text="StdOut",relief=RAISED, width=24, bg="light yellow",font=("Times", 16))
        stderr_title = Label(self.frame,text="StdErr",relief=RAISED, width=24, bg="light yellow",font=("Times", 16))
        stdout_title.grid(row=0, column=0)
        stderr_title.grid(row=0, column=2)        

        outputPanel = Text(self.frame, wrap='word', relief=RIDGE, bd = 2, height = 36, width=70)
        outputPanel.grid(column=0, row=1)
        stdout_scr = Scrollbar(self.frame, command=outputPanel.yview)
        stdout_scr.grid(row=1, column=1, sticky='nsew')
        outputPanel['yscrollcommand'] = stdout_scr.set
        sys.stdout = self.Redirector(outputPanel)

        errorPanel = Text(self.frame, wrap='word', relief=RIDGE, bd = 2, height = 36, width=70)
        errorPanel.grid(column=2, row=1)
        stderr_scr = Scrollbar(self.frame, command=errorPanel.yview)
        stderr_scr.grid(row=1, column=3, sticky='nsew')
        errorPanel['yscrollcommand'] = stderr_scr.set
        sys.stderr = self.Redirector(errorPanel)

        return

    class Redirector(object):

        def __init__(self, text_area):
            self.text_area = text_area
            self.text_area.see(END)
    
        def write(self, str):
            self.text_area.insert(END, str)
            self.text_area.see(END)

        def flush(self):
            self.text_area.see(END)

    
