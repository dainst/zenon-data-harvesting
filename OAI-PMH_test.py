#Here they have tried to add https://pypi.python.org/pypi as a repository.
#To add it as a repository,
#1.) Go to Settings
#2.) Project interpreter
#3.) Click the + sign on top right edge
#4.) Go to manage repositories,
#5.) Press the + Sign, then add https://pypi.python.org/pypi
#6.) Press Ok
#funktioniert dann
import json
import re
from sickle import Sickle
sickle = Sickle('https://www.e-periodica.ch/oai/dataprovider') # initialisiert Verbindung
records_900 = sickle.ListIdentifiers(metadataPrefix='oai_dc', set='ddc:900') #sammelt Header
record_identifiers={}
doi_list=[]
item_number=0
record=0
for record in records_900:
    if item_number > 9:
        break
    record_splitted=re.split('identifier',str(record))
    doi=record_splitted[1][1:-2]
    doi_list.append(doi)
    item_number+=1
    record_identifiers["records_900"] = doi_list
    with open("records.json", "w") as write_file:
            json.dump(record_identifiers, write_file)
