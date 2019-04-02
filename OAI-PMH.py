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
from sickle import Sickle
sickle = Sickle('https://www.e-periodica.ch/oai/dataprovider') # initialisiert Verbindung
records_900 = sickle.ListIdentifiers(metadataPrefix='oai_dc', set='ddc:900')
records_930 = sickle.ListIdentifiers(metadataPrefix='oai_dc', set='ddc:930')
records_940 = sickle.ListIdentifiers(metadataPrefix='oai_dc', set='ddc:940')
record_identifiers={}
record_list=[]
for item in records_900:
    print(item)
    record_list.append(item)
record_identifiers["records_900"]=record_list
record_list=[]
for item in records_900:
    print(item)
    record_list.append(item)
record_list=[]
record_identifiers["records_930"]=record_list
for item in records_900:
    print(item)
    record_list.append(item)
record_identifiers["records_940"]=record_list
