#!/usr/bin/env python
#Author: Craig Lage
#Date: 10-May-15
# These files contains various subroutines
# needed to run the LSST Simulator
# This code sends an E-Mail in the event of a failure

import sys, smtplib
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart

#************************************* SUBROUTINES ***********************************************

def Send_Warning(message_subject, message_text):
    to_list=['pgee@physics.ucdavis.edu',]# 'ucdavislsst@gmail.com']
    server=smtplib.SMTP('ucdavis-edu.mail.protection.outlook.com', 25)
    server.starttls()
    msg = MIMEMultipart()
    msg['From']='ucdavislsst@gmail.com'
    msg['Subject']=message_subject
    msg.attach(MIMEText(message_text,'plain'))
    msg['To']=','.join(to_list)
    text=msg.as_string()
    server.sendmail('ucdavislsst@gmail.com', to_list, text)
    server.quit()
    return 
