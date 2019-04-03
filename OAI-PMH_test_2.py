import json
import re
import time
from sickle import Sickle
from pymarc import Record, Field
import requests
sickle = Sickle('https://www.e-periodica.ch/oai/dataprovider') # initialisiert Verbindung
records_900 = sickle.ListIdentifiers(metadataPrefix='oai_dc', set='ddc:900') #sammelt Header
record_identifiers={}
doi_list=[]
item_number=0
record=0
print(time.clock())
for record in records_900:
    if item_number > 3:
        break
    #print(record)
    record_splitted=re.split('identifier',str(record))
    doi=record_splitted[1][1:-2]
    doi_list.append(doi)
    item_number+=1
    record_identifiers["records_900"] = doi_list
print(time.clock())
record_number=1
for doi in record_identifiers["records_900"]:
    sickle2 = Sickle('https://www.e-periodica.ch/oai/dataprovider')
    content_list=sickle2.GetRecord(identifier=doi, metadataPrefix = 'oai_dc')
    content_list=list(content_list)
    print(content_list)
    recent_record=Record()
    if content_list[0][1][0]!=None:
        for title in content_list[0][1]:
            recent_record.add_field(Field(tag='245', indicators = ['0', '0'], subfields = ['a', title]))
    filename='record'+str(record_number)+'.dat'
    with open(filename, 'wb') as out:
        out.write(recent_record.as_marc21())
    record_number+=1

#https://www.loc.gov/marc/dccross.html Erklärung mapping dublin core auf MARC21
#Erklärung zu MARC: http://www.loc.gov/marc/umb/ http://www.loc.gov/marc/marcdocz.html