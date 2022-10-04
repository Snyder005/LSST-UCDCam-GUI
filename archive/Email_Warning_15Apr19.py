#!/usr/bin/env python
#Author: Craig Lage, Perry Gee
#Date: 15-Apr-19
# These files contains various subroutines
# needed to run the LSST Simulator
# This code sends an E-Mail in the event of a failure

import sys, smtplib
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart

#************************************* SUBROUTINES ***********************************************

def Send_Warning(message_subject, message_text):
    to_list=['cslage@ucdavis.edu', 'craig.lage@yahoo.com', 'pgee@ucdavis.edu'] #'AndrewKBradshaw@gmail.com', 'dapolin@ucdavis.edu', 'tyson@physics.ucdavis.edu', 'pgee2000@gmail.com']
    server=smtplib.SMTP('74.125.197.109', 587)
    server.starttls()
    server.login('ucdavislsst@gmail.com','Nerdlet14')

    for to_addr in to_list:
        msg = MIMEMultipart()
        msg['From']='ucdavislsst@gmail.com'
        msg['Subject']=message_subject
        msg.attach(MIMEText(message_text,'plain'))
        msg['To']=to_addr
        text=msg.as_string()
        server.sendmail('ucdavislsst@gmail.com', to_addr, text)
    server.quit()
    return 

