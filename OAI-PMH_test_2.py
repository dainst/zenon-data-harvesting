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
    if item_number > 9:
        break
    print(record)
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
    print(type(content_list))
    import xml.etree.ElementTree as ET

    for child in content_list:
        if child[1][0] is not None:
            print(f"Element: {child[0]}, content: {child[1]}")

    #filename='record_nr' + str(record_number) + '.xml'
    #with open(filename, 'w') as file:
        #file.write(text)
    record_number+=1
from pymarc import Record, Field
record = Record()
record.add_field(
    Field(
        tag = '245',
        indicators = ['0','1'],
        subfields = [
            'a', 'The pragmatic programmer : ',
            'b', 'from journeyman to master /',
            'c', 'Andrew Hunt, David Thomas.'
        ]))
with open('file.dat', 'wb') as out:
    out.write(record.as_marc())
#https://www.loc.gov/marc/dccross.html Erklärung mapping dublin core auf MARC21
#Erklärung zu MARC: http://www.loc.gov/marc/umb/ http://www.loc.gov/marc/marcdocz.html