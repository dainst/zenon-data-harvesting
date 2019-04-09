import re
from sickle import Sickle
from pymarc import Record, Field
from langdetect import detect
import arrow
import json
language_codes=open('languages.json', 'r')
language_codes=json.load(language_codes)
time=arrow.now().format('YYMMDD')
articles={'en': ['the','a', 'an'], 'fr':['la','le','les','un', 'une', 'l\'', 'il'], 'es':['el','lo','la','las','los',
    'uno' 'un', 'unos', 'unas', 'una'], 'de':['das', 'der', 'ein', 'eine', 'die'], 'it':['gli', 'i','le', 'la', 'l\'',
    'lo', 'il', 'gl\'', 'l']}
sickle = Sickle('https://www.e-periodica.ch/oai/dataprovider') # initialisiert Verbindung
records_900 = sickle.ListIdentifiers(metadataPrefix='oai_dc', set='ddc:930') #sammelt Header
record_identifiers={}
doi_list=[]
item_number=0
record=0
for record in records_900:
    if item_number > 70:
        break
    record_splitted=re.split('identifier',str(record))
    doi=record_splitted[1][1:-2]
    doi_list.append(doi)
    item_number+=1
    record_identifiers["records_930"] = doi_list
record_number=1
for doi in record_identifiers["records_930"]:
    sickle2 = Sickle('https://www.e-periodica.ch/oai/dataprovider')
    content_list=sickle2.GetRecord(identifier=doi, metadataPrefix = 'oai_dc')
    content_list=list(content_list)
    recent_record=Record()
    '''00-04 - Rekordlänge
05 n
06 m
07 b
08 leer lassen
09 a
10 leer lassen
11 leer lassen
12 - 16 leer lassen
17 u
18 u
19 leer lassen

Kommt jetzt 4500?
20 - 22 füllt sich das automatisch?
23
'''
    title=content_list[0][1][0]
    lang = detect(title)
    print(title, record_number)
    recent_record.leader = recent_record.leader[:5] + "ups" + recent_record.leader[8:]
    #print(recent_record.leader)
    recent_record.add_field(Field(tag='040', indicators = [' ', ' '], subfields = ['a', 'eperiodica', 'd', 'DE-2553']))
    recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'online publication']))
    recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'a rom']))
    recent_record.add_field(Field(tag='336', indicators = [' ', ' '], subfields = ['a', 'text', 'b', 'txt', '2', 'rdacontent']))
    recent_record.add_field(Field(tag='042', indicators=[' ', ' '], subfields=['a', 'dc']))
    recent_record.add_field(Field(tag='006', indicators=None, subfields=None, data=u'm        u        '))
    recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'cuuuuu   uuauu'))
    recent_record.add_field(Field(tag='024', indicators = ['7', ' '], subfields = ['a', content_list[14][1][2][4:], '2', 'doi']))
    sprachcode=language_codes[lang]
    data_008=str(time)+'s'+ content_list[6][1][0][:5] + '    ' + 'sz' + '                  ' + sprachcode +' d'
    recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
    creator_number=0
    for creator in content_list[1][1]:
        if creator not in [None,'[s.n.]']:
            if '\u0153' in creator:
                creator=creator.replace('œ', 'oe')
            creator_number+=1
            if creator_number==1:
                recent_record.add_field(Field(tag='100', indicators = ['1', ' '], subfields = ['a', creator]))
            else:
                recent_record.add_field(Field(tag='700', indicators = ['1', ' '], subfields = ['a', creator]))
    nonfiling_characters=0
    if '\u0153' in title:
        title=title.replace('œ', 'oe')
    if lang in articles.keys():
        first_word=(title.split()[0]).lower()
        if first_word in articles[lang]:
            nonfiling_characters=str(len(first_word)+1)
    if creator_number==0: #title
        recent_record.add_field(Field(tag='245', indicators = ['0', nonfiling_characters], subfields = ['a', title]))
        #weitere Bearbeitungen notwendig!!!
    else: #title
        recent_record.add_field(Field(tag='245', indicators = ['1', nonfiling_characters], subfields = ['a', title]))
    if content_list[4][1][0] not in [None,'[s.n.]'] and content_list:
        recent_record.add_field(Field(tag='260', indicators = [' ', ' '],
                                      subfields = ['b', content_list[4][1][0], 'c', content_list[6][1][0][:5]]))
    recent_record.add_field(Field(tag='856', indicators = ['4', '1'],
                            subfields = ['u', content_list[14][1][0], 'z', 'Table of Contents']))
    recent_record.add_field(Field(tag='856', indicators = ['4', '1'],
                                  subfields = ['u', content_list[14][1][1], 'z', 'application/pdf']))
    recent_record.add_field(Field(tag='856', indicators = ['4', '1'],
                                  subfields = ['u', 'https://doi.org/'+content_list[14][1][2][4:], 'z', 'Table of Contents']))

    filename='record'+str(record_number)+'.mrc'
    with open(filename, 'wb') as out:
            out.write(recent_record.as_marc21())
    record_number+=1

#https://www.loc.gov/marc/dccross.html Erklärung mapping dublin core auf MARC21
#Erklärung zu MARC: http://www.loc.gov/marc/umb/ http://www.loc.gov/marc/marcdocz.html