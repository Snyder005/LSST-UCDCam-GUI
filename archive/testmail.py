import imaplib
import pdb
import email
import datetime

mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('ucdavislsst', 'Nerdlet14')
mail.list()
# Out: list of "folders" aka labels in gmail.
mail.select("inbox") # connect to inbox.
result, data = mail.search(None, "ALL")
result, data = mail.uid('search', None, '(HEADER Subject "Dylos")')
pdb.set_trace() 
ids = data[0] # data is a list.
id_list = ids.split() # ids is a space separated string
latest_email_id = id_list[-1] # get the latest
 
result, data = mail.fetch(latest_email_id, "(RFC822)") # fetch the email body (RFC822) for the given ID
 
raw_email = data[0][1] # here's the body, which is raw text of the whole email
# including headers and alternate payloads
email_message = email.message_from_string(raw_email)
 
print email_message['To']
 
print email.utils.parseaddr(email_message['From']) # for parsing "Yuji Tomita" <yuji@grovemade.com>
 
#print email_message.items()

pdb.set_trace()
