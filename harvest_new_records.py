import aegyptiaca_modularized
import berrgk_modularized
import BMCR_modularized
import cipeg_modularized
import efb_modularized
# import eperiodica_modularized
import germania_modularized
# import hsozkult_modularized
import bjb_modularized
# import jdi_modularized
import late_antiquity_modularized
import maa_journal_current_modularized
import write_error_to_logfile
import smtplib
from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
from datetime import datetime

# logfiles vorhanden für:

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")

logfile = 'logfile_' + timestampStr

return_string = ''

print('beep')

for harvesting_script in [aegyptiaca_modularized, berrgk_modularized, cipeg_modularized, BMCR_modularized, bjb_modularized,
                          efb_modularized, germania_modularized, # hsozkult_modularized, eperiodica_modularized, jdi_modularized
                          late_antiquity_modularized, maa_journal_current_modularized]:
    try:
        return_string += harvesting_script.harvest()
        print(return_string)
    except Exception as e:
        write_error_to_logfile.write(e)

print(return_string)

# set up the SMTP server
s = smtplib.SMTP(host="securesmtp.t-online.de", port=587)
s.starttls()
s.login("helena.nebel@t-online.de", 'DW!&FwvmE')


# For each contact, send the email:
msg = MIMEMultipart()       # create a message

# add in the actual person name to the message template
message = 'bla'

# setup the parameters of the message
msg['From']='Helena Nebel'
msg['To']='helena.nebel@dainst.de' # ändern
msg['Subject']= "Ergebnisse des Harvesting-Prozesses am " + timestampStr

#with open(logfile, 'r') as new_logfile:
    #msg.attach(MIMEText(new_logfile.read(), "plain"))

# send the message via the server set up earlier.
s.send_message(msg)

# zwei Emails senden.