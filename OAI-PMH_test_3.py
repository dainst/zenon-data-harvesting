import json
import re
import time
from sickle import Sickle
import requests
sickle = Sickle('https://www.e-periodica.ch/oai/dataprovider') # initialisiert Verbindung
records_900 = sickle.ListIdentifiers(metadataPrefix='oai_dc', set='ddc:900') #sammelt Header
record_identifiers={}
doi_list=[]
item_number=0
record=0
print(time.clock())
for record in records_900:
    print(item_number)
    #if item_number > 9:
        #break
    #print(record)
    record_splitted=re.split('identifier',str(record))
    doi=record_splitted[1][1:-2]
    doi_list.append(doi)
    item_number+=1
    record_identifiers["records_900"] = doi_list
print(time.clock())