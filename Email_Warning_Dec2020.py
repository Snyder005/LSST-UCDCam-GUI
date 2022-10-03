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
lsst_addr="ucdavislsst@gmail.com"

def Send_Warning(message_subject, message_text, adminOnly=False):
    to_list=[lsst_addr, 'pgee2000@gmail.com', 'cslage@physics.ucdavis.edu']
    if not adminOnly:
        #to_list.extend(['pgee@physics.ucdavis.edu', 'pgee2013@gmail.com',])
        to_list.extend(['AndrewKBradshaw@gmail.com','dapolin@ucdavis.edu', 'tyson@physics.ucdavis.edu'])
    outside_list = []
    # First send waring for all ucdavis addrs to default server at solid.physics.ucdavis.edu
    for to_addr in to_list:
        try:
            to_addr.index("ucdavis.edu")
        except ValueError:
            outside_list.append(to_addr)
    for to_addr in outside_list:
        to_list.remove(to_addr)
    if len(to_list) > 0:
        msg = MIMEMultipart()
        msg['From']=lsst_addr
        msg['Subject']=message_subject
        msg.attach(MIMEText(message_text,'plain'))
        msg['To']=','.join(to_list)
        text=msg.as_string()
        server=smtplib.SMTP('ucdavis-edu.mail.protection.outlook.com', 25)
        server.starttls()
        server.sendmail(lsst_addr, to_list, text)
        server.quit()
    # The to_list should be cleansed of any ucdavis.edu clients at this point
    server=smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(lsst_addr,'Nerdlet14')
    msg = MIMEMultipart()
    msg['From']=lsst_addr
    msg['Subject']=message_subject
    msg.attach(MIMEText(message_text,'plain'))
    msg['To']=','.join(outside_list)
    text=msg.as_string()
    server.sendmail(lsst_addr, outside_list, text)
    server.quit()
    return 
