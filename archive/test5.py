import Email_Warning as ew
import time
def Send_Warning(subject, warning, adminOnly=True):
    try:
        subject = "Dylos Warning issued " + time.asctime()
        w_file = open('send_warning', 'w')
        w_file.write(subject + ":: ")
        w_file.write(warning)
        w_file.close()
        print ("Warning saved to send_warning")

    except:
        print "Dylos warning did not get sent"

Send_Warning("Test Dylos message", "This is (hopefully) the last test.  Please respond to this email if you get it.", True)
