import subprocess 
import time
import os
import sys, smtplib
import imaplib
import email
import datetime
import Email_Warning as ew
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart

#   This sends just to the ucdavislsst.gmail.com user
def Monitor_Warning(subject, message, adminOnly=True):
    if subject.endswith('@'):
        subject = subject + time.asctime()
    ew.Send_Warning(subject, message, adminOnly=adminOnly)

#  This python scripts check to be sure that the particle_graph is sent regularly
#  and that any send_warning message sent has been received by ucdavislsst@gmail.com
#  if not received, it is resent to the smtp.gmail.com server
def Check_Email(subject):
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login('ucdavislsst', 'Nerdlet14')
    mail.list()
    # Out: list of "folders" aka labels in gmail.
    mail.select("inbox") # connect to inbox.
    result, data = mail.uid('search', None, '(HEADER Subject "%s")'%subject)
    ids = data[0] # data is a list.
    if len(ids) <= 0:
        return 0
    return 1
    id_list = ids.split() # ids is a space separated string
    latest_email_id = id_list[-1] # get the latest
 
    result, data = mail.fetch(latest_email_id, "(RFC822)") # fetch the email body (RFC822) for the given ID
 
    raw_email = data[0][1] # here's the body, which is raw text of the whole email
    # including headers and alternate payloads
    email_message = email.message_from_string(raw_email)
    print email_message['To']
    print email.utils.parseaddr(email_message['From']) #
    return len(id_list) 


#   write a running message
Particle_Graph_Warning = "Particle graph warning@"
Send_Message_Warning = "Send_message not received"
print "Monitor running " + time.asctime()
#   check to be sure that the particle graph omega is being updated
command = 'ssh root@omega stat -c "%Y" /var/www/html/storm/particle_graph.png'
proc=subprocess.Popen(command.split(), stdout=subprocess.PIPE)
soutput,sinput=proc.communicate()
lines = soutput.split('\n')
ctime = float(lines[0])
minutes_since = (time.time() - ctime)/60.0
if minutes_since > 60.0:
    message = "particle_graph.png has not been updated in %f minutes"%(minutes_since,)
    found = Check_Email(Particle_Graph_Warning + time.strftime("%a %B %d"))
    if not found:
        print message
        Monitor_Warning(Particle_Graph_Warning, message)
    else:
        print "particle graph warning already sent today"
#   check to be sure that the last send message was actually received
warning_file = "/sandbox/lsst/lsst/GUI/particles/send_warning"
if os.path.exists(warning_file):
    mtime = os.path.getmtime(warning_file)
    minutes_since = (time.time() - mtime)/60.0
    rfile = open(warning_file, 'r')
    lines = rfile.readlines()
    subject = None
    for line in lines:
        if line.startswith("Dylos Warning"):
            index = line.find(":: ")
            if index > 0:
                subject = line[:index]
                contents = line[index+3:]
    if not subject:
        Monitor_Warning("Message format warning", "Unexpected Dylos send_message: " + line)
        print "Send_warning found but badly formatted.  Warning sent."
    else:
        if not Check_Email(subject):
            if minutes_since > 10.0:
                message = "send_warning not received in %f minutes.  Resending: %s"%(minutes_since, contents)
                print message
                # send this message to the whole list through the outside server
                Monitor_Warning(subject, message, date=False) #, inside=False)
            else:
                pass
        else:
            pass
