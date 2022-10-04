import Email_Warning as ew
import time

#   This routine both sends a warning to the email list in Email_Warning
#   and also writes the warning to disk under the file named "send_warning"
def Warning(warning):
    try:
        subject = "Dylos Warning issued " + time.asctime()
        w_file = open('send_warning', 'w')
        w_file.write(subject + ":: ")
        w_file.write(warning)
        w_file.close()
        ew.Send_Warning(subject, warning)
    except:
        print ("ERROR OCCURRED while sending warning to email server")

Warning("this is a test warning")
