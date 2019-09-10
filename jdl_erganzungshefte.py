import urllib.request, urllib.parse
import re
import urllib.parse, urllib.request
from pymarc import Record, Field
import arrow
import csv
import language_codes
from nltk.tokenize import RegexpTokenizer
from bs4 import BeautifulSoup
import ast
import spacy
from langdetect import detect

language_articles = {'eng': ['the', 'a', 'an'], 'fre': ['la', 'le', 'les', 'un', 'une', 'l\'', 'il'],
                     'spa': ['el', 'lo', 'la', 'las', 'los',
                             'uno' 'un', 'unos', 'unas', 'una'], 'ger': ['das', 'der', 'ein', 'eine', 'die'],
                     'ita': ['gli', 'i', 'le', 'la', 'l\'',
                             'lo', 'il', 'gl\'', 'l']}

def create_245_and_246(recent_record, title, nonfiling_characters, author_nr):
    recent_record.add_field(Field(tag='245', indicators=[str(author_nr), nonfiling_characters], subfields=['a', title]))

def determine_nonfiling_characters(recent_record, title, date_of_publication, language):
    print(date_of_publication, language)
    nonfiling_characters = 0
    recent_record.add_field(Field(tag='041', indicators=['1', ' '], subfields=['a', language]))
    if language in language_articles.keys():
        first_word = (title.split()[0]).lower()
        if first_word in language_articles[language]:
            nonfiling_characters = str(len(first_word) + 1)
    data_008 = str(time_str) + 's' + date_of_publication + '    ' + 'gw ' + ' |   o     |    |' + language + ' d'
    recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
    return nonfiling_characters

def doi_is_valid(doi):
    try:
        req = urllib.request.Request(doi)
        with urllib.request.urlopen(req) as response:
            doi_page = response.read()
        return True
    except:
        return False

def create_new_record(item, out, volume_url, volume_year, date_published_online, date_of_publication, volume):
    doi=None
    recent_record = Record(force_utf8=True)
    recent_record.add_field(
        Field(tag='336', indicators=[' ', ' '], subfields=['a', 'text', 'b', 'txt', '2', 'rdacontent']))
    recent_record.add_field(
        Field(tag='337', indicators=[' ', ' '], subfields=['a', 'computer', 'b', 'c', '2', 'rdamedia']))
    recent_record.add_field(
        Field(tag='338', indicators=[' ', ' '], subfields=['a', 'online resource', 'b', 'cr', '2', 'rdacarrier']))
    title=item.find('mods:title').text.split(' / ')[1]
    author_nr = 0
    for author in item.find_all('mods:name'):
        author_name = ""
        if author.find_all('mods:roleTerm')!=[]:
            if author_name==author.find('mods:displayForm').text:
                continue
            author_name = author.find('mods:displayForm').text
            if author_nr == 0:
                recent_record.add_field(Field(tag='100', indicators=['1', ' '], subfields=['a', author_name]))
                author_nr += 1
            else:
                recent_record.add_field(Field(tag='700', indicators=['1', ' '], subfields=['a', author_name]))
                author_nr = author_nr

    physical_info = item.find('mods:physicalDescription')
    recent_record.add_field(Field(tag='006', indicators=None, data='m        d        '))
    recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data='cr  uuu    a uuuuu'))
    if physical_info!=None:
        pages = physical_info.find('mods:extent', unit='pages').text
        ill = physical_info.find('mods:extent', unit='illustrations').text
        recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', pages, 'b', ill]))
    language = item.find('mods:language')
    if language!=None:
        language = language.find('mods:languageTerm').text
    else:
        language = 'ger'
    identifier_info = item.find('mods:identifier', type='doi')
    if identifier_info!=None:
        doi="http://www.doi.org/"+identifier_info.text
        if doi_is_valid(doi)==True:
            recent_record.add_field(Field(tag='024', indicators=['7', ' '], subfields=['a', doi, '2', 'doi']))
    recent_record.add_field(Field(tag='040', indicators=[' ', ' '], subfields=['a', 'DE-16', 'd', 'DE-2553']))
    recent_record.add_field(Field(tag='533', indicators=[' ', ' '],
                                  subfields=['a', 'Online edition', 'b', 'Heidelberg', 'c', 'Heidelberg UB', 'd',
                                             date_published_online.strip('.').split('.')[-1], 'e', 'Online resource']))
    recent_record.leader = recent_record.leader[:5] + 'nab a       uu ' + recent_record.leader[20:]
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'arom']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', '2019xhnxjdi']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'online publication']))
    print(title)
    nonfiling_characters = determine_nonfiling_characters(recent_record, title, date_of_publication, language)
    create_245_and_246(recent_record, title, nonfiling_characters, author_nr)
    if doi != None:
        recent_record.add_field(Field(tag='856', indicators=['4', '0'],
                                      subfields=['z', 'application/pdf', 'u', doi]))
    recent_record.add_field(Field(tag='856', indicators=['4', '2'],
                                  subfields=['z', 'Table of Contents', 'u', volume_url]))
    subject_info = item.find('mods:subject')
    if subject_info!=None:
        persons = subject_info.find_all('mods:name', type='personal')
        for person in persons:
            person_name = person.find('mods:displayForm').text
            if ',' in person_name:
                first_indicator = '1'
            else:
                first_indicator = '0'
            person_authority = person['authority']
            recent_record.add_field(Field(tag='600', indicators=[first_indicator, '7'],
                                          subfields=['a', person_name, '2', person_authority]))
        corporations = subject_info.find_all('mods:name', type='corporate')
        for corporation in corporations:
            corporation_name = corporation.find('mods:displayForm').text
            corporation_authority = corporation['authority']
            recent_record.add_field(Field(tag='610', indicators=['2', '7'],
                                          subfields=['a', corporation_name, '2', corporation_authority]))
        geographics = subject_info.find_all('mods:geographic')
        for geographic in geographics:
            geographic_name = geographic.text
            geographic_authority = geographic['authority']
            recent_record.add_field(Field(tag='651', indicators=[' ', '7'],
                                          subfields=['a', geographic_name, '2', geographic_authority]))
        topics = subject_info.find_all('mods:topic')
        for topic in topics:
            topic_name = topic.text
            topic_authority = topic['authority']
            recent_record.add_field(Field(tag='650', indicators=[' ', '7'],
                                          subfields=['a', topic_name, '2', topic_authority]))
    print(volume, volume_year, volume_url)
    if int(date_of_publication)<1919:
        recent_record.add_field(Field(tag='264', indicators=[' ', '1'],
                                      subfields=['a', 'Berlin', 'b', 'Georg Reimer', 'c', date_of_publication]))

    else:
        recent_record.add_field(Field(tag='264', indicators=[' ', '1'],
                                      subfields=['a', 'Berlin; Leipzig', 'b', 'Walter de Gruyter & Co.', 'c', date_of_publication]))

    if int(date_of_publication)<1918:
        recent_record.add_field(Field(tag='LKR', indicators=[' ', ' '],
                                      subfields=['a', 'ANA', 'b', '001578267', 'l', 'DAI01',
                                                 'm', title, 'n', 'Jahrbuch des Kaiserlich Deutschen Archäologischen Instituts' + ', ' +
                                                 volume + ' (' + volume_year + ')']))
    else:
        recent_record.add_field(Field(tag='LKR', indicators=[' ', ' '],
                                      subfields=['a', 'ANA', 'b', '001578267', 'l', 'DAI01',
                                                 'm', title, 'n', 'Jahrbuch des Deutschen Archäologischen Instituts : JdI' + ', ' +
                                                 volume + ' (' + volume_year + ')']))
    #Angaben anpassen!
    out.write(recent_record.as_marc21())

out=None
time_str = arrow.now().format('YYMMDD')
basic_url = 'https://digi.ub.uni-heidelberg.de/diglit/jdi_ergh'
record_nr = 0
user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
values = {'name': 'Helena Nebel',
          'location': 'Berlin',
          'language': 'Python'}
headers = {'User-Agent': user_agent}
data = urllib.parse.urlencode(values)
data = data.encode('ascii')
req = urllib.request.Request(basic_url, data, headers)
with urllib.request.urlopen(req) as response:
    yearbook_page = response.read()
yearbook_page = yearbook_page.decode('utf-8')
yearbook_page = BeautifulSoup(yearbook_page, 'html.parser')
volume_years = [item.text for item in yearbook_page.find('table', class_='tabelle-baendeliste').find_all('span', class_='publ-daten-schwarz')]
volume_urls = [item['href'] for item in yearbook_page.find('table', class_='tabelle-baendeliste').find_all('a')]
volumes_already_processed = []
for volume_url in volume_urls:
    print(volume_url)
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
    values = {'name': 'Helena Nebel',
              'location': 'Berlin',
              'language': 'Python'}
    headers = {'User-Agent': user_agent}
    data = urllib.parse.urlencode(values)
    data = data.encode('ascii')
    req = urllib.request.Request(volume_url, data, headers)
    with urllib.request.urlopen(req) as response:
        volume_page = response.read()
    volume_page = volume_page.decode('utf-8')
    volume_soup = BeautifulSoup(volume_page, 'html.parser')
    date_published_online = volume_soup.find('div', id='publikationsdatum').text.strip().split()[-1]
    print(date_published_online)
    volume_year=volume_years[record_nr].split('(')[0].split(', ')[-1]
    mets_url=volume_url.split("?")[0]+'/mets'
    webFile = urllib.request.urlopen(mets_url)
    xml_soup=BeautifulSoup(webFile, 'xml')
    record_nr+=1
    if volume_url not in volumes_already_processed:
        volumes_already_processed.append(volume_url)
        out = open('records/JdI/JdI_ergh' + volume_year.split('/')[0] + '.mrc', 'wb')
    else:
        out = out
    date_of_publication = xml_soup.find_all('mods:mods')[0].find('mods:originInfo').find('mods:dateIssued', keyDate='yes').text
    if '(' in date_of_publication:
        date_of_publication = date_of_publication.split('(')[1].replace(')')
    volume=xml_soup.find_all('mods:mods')[0].find('mods:number').text
    for item in xml_soup.find_all('mods:mods')[:1]:
        create_new_record(item, out, volume_url, volume_year, date_published_online, date_of_publication, volume)







'''<mods:name type="personal" authority="gnd" authorityURI="http://d-nb.info/gnd/" valueURI="http://d-nb.info/gnd/101110464"><mods:namePart type="family">Michaelis</mods:namePart><mods:namePart type="given">Adolf</mods:namePart><mods:displayForm>Michaelis, Adolf</mods:displayForm>'''