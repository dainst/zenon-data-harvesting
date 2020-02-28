import os
from webdav3.client import Client
import write_error_to_logfile
from datetime import datetime

import aegyptiaca_modularized
import antiquite_modularized
import berrgk_modularized
# import bjb_modularized
import BMCR_modularized
import cipeg_modularized
import efb_modularized
import eperiodica_akb_002_modularized
import eperiodica_bat_001_modularized
import eperiodica_snr_003_modularized
# import germania_modularized >>> nachfragen, was jetzt damit ist!
import gnomon_modularized
import hsozkult_modularized
# import jdi_modularized
import late_antiquity_modularized_new
import maa_journal_current_modularized
import groma_modularized
import world_prehistory
import kokalos
import sardinia_corsica_baleares_modularized

# logfiles vorhanden für:

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")

return_string = ''
new_dir = 'harvest_' + timestampStr
path = '/home/hnebel/Programmierung/zenon-data-harvesting/records/'
error_path = '/home/hnebel/Programmierung/zenon-data-harvesting/logfiles_debugging/'
if new_dir not in os.listdir(path):
    os.mkdir(path + new_dir)
path_for_cumulus = '/home/hnebel/Programmierung/zenon-data-harvesting/records/' + new_dir
path = '/home/hnebel/Programmierung/zenon-data-harvesting/records/' + new_dir + '/'
print(path)
for harvesting_script in [aegyptiaca_modularized, antiquite_modularized, berrgk_modularized, BMCR_modularized,
                          cipeg_modularized,
                          efb_modularized,
                          eperiodica_akb_002_modularized, eperiodica_bat_001_modularized, eperiodica_snr_003_modularized,
                          gnomon_modularized,
                          groma_modularized,
                          hsozkult_modularized,
                          late_antiquity_modularized_new,
                          maa_journal_current_modularized,
                          world_prehistory,
                          sardinia_corsica_baleares_modularized,
                          kokalos
                          ]:  # bjb_modularized, germania_modularized, jdi_modularized
    try:
        print(harvesting_script)
        new_return_string = harvesting_script.harvest(path)
        return_string += new_return_string
        print(new_return_string)
        write_error_to_logfile.comment(new_return_string)
    except Exception as e:
        write_error_to_logfile.write(e)

print(return_string)
write_error_to_logfile.comment(return_string)
# alle Dateien mit size 0 Bytes löschen:
for file in os.listdir(path_for_cumulus):
    size = os.path.getsize(path + file)
    print(size)
    if size == 0:
        os.remove(path + file)

options = {
    'webdav_hostname': 'https://cumulus.dainst.org/remote.php/webdav',
    'webdav_login':    'hnebel',
    'webdav_password': '9J_m3na'
}
client = Client(options)
client.Verify = False
client.mkdir('Periodicals_continuously_harvested/harvest_' + timestampStr)
# Directory mit Datum auf Cumulus erstellen
client.upload(remote_path='Periodicals_continuously_harvested/harvest_' + timestampStr, local_path=path)
client.mkdir('Periodicals_continuously_harvested/harvest_' + timestampStr + '_logfiles_debugging')
# Directory mit Datum auf Cumulus erstellen
client.upload(remote_path='Periodicals_continuously_harvested/harvest_' + timestampStr + '_logfiles_debugging',
              local_path='/home/hnebel/Programmierung/zenon-data-harvesting/logfiles_debugging/')

# lokales Directory mit den erstellten Files hochladen

# bei 404 Fehlerbehandlung anpassen.
# Error! Code: HTTPError, Message, HTTP Error 404: Not Found,
# Type, <class 'urllib.error.HTTPError'>, File, hsozkult_modularized.py, Line 104
# logfiles hochladen!
