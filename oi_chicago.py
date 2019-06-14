import urllib.parse, urllib.request
from pymarc import Record, Field, MARCReader
import arrow
import language_codes
from bs4 import BeautifulSoup
import os
from pdf2image import convert_from_path
import tempfile
from nltk.tokenize import RegexpTokenizer
import ast
import re
from nameparser import HumanName
from langdetect import detect
import spacy
from scipy import spatial
import unicodedata
import pymarc
import xml.etree.ElementTree as ET

language_articles={'eng': ['the','a', 'an'], 'fre':['la','le','les','un', 'une', 'l\'', 'il'], 'spa':['el','lo','la','las','los',
                                                                                                      'uno' 'un', 'unos', 'unas', 'una'], 'ger':['das', 'der', 'ein', 'eine', 'die'], 'ita':['gli', 'i','le', 'la', 'l\'',
                                                                                                                                                                                             'lo', 'il', 'gl\'', 'l']}

def create_new_record(out, xml_soup, pdfs, url, record_nr):
    time_str = arrow.now().format('YYMMDD')
    recent_record = Record(force_utf8=True)
    recent_record.add_field(Field(tag='006', indicators=None, data='m        d        '))
    recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'tz'))
    old_008 = xml_soup.find('controlfield', tag='008').text
    language = old_008[35:38]
    year=''
    if len(xml_soup.find_all('datafield', tag='264'))>=1:
        year = re.findall(r'(\d{4})',xml_soup.find_all('datafield', tag='264')[0].find('subfield', code='c').text)[0]
    if len(xml_soup.find_all('datafield', tag='260'))!=0 and year=='':
        year = re.findall(r'(\d{4})',xml_soup.find_all('datafield', tag='260')[0].find('subfield', code='c').text)[0]
    if year=='':
        year=input('Bitte geben Sie das Jahr ein: ')
    print(year)
    data_008 = time_str+'s'+year+'    '+'ilu'+' |   o     |    |'+old_008[-5:]
    recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
    recent_record.add_field(Field(tag='040', indicators=[' ', ' '], subfields=['a', 'OI', 'b', 'eng', 'd', 'DE-2553', 'e', 'rda']))
    recent_record.add_field(Field(tag='041', indicators=['1', ' '], subfields=['a', language]))
    recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', '1 online resource']))
    recent_record.add_field(Field(tag='336', indicators=[' ', ' '], subfields=['a', 'text', 'b', 'txt', '2', 'rdacontent']))
    recent_record.add_field(Field(tag='337', indicators=[' ', ' '], subfields=['a', 'computer', 'b', 'c', '2', 'rdamedia']))
    recent_record.add_field(Field(tag='338', indicators=[' ', ' '], subfields=['a', 'online resource', 'b', 'cr', '2', 'rdacarrier']))
    recent_record.leader = recent_record.leader[:5] + 'mmb a       uu ' + recent_record.leader[20:]
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'ebookoa0619']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', '2019xhnxoi']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'online publication']))
    ind_1_245 = ' '
    if xml_soup.find('datafield', tag='100') != None:
        ind_1_245 = '1'
        for responsible in xml_soup.find_all('datafield', tag='100'):
            subfields_100=[]
            for subfield in xml_soup.find('datafield', tag='100').find_all('subfield'):
                subfields_100.append(subfield['code'])
                subfields_100.append(subfield.text)
            recent_record.add_field(Field(tag='100', indicators=[responsible['ind1'], responsible['ind2']], subfields=subfields_100))
    if xml_soup.find('datafield', tag='700') != None:
        ind_1_245 = '1'
        for responsible in xml_soup.find_all('datafield', tag='700'):
            subfields_700=[]
            for subfield in xml_soup.find('datafield', tag='700').find_all('subfield'):
                subfields_700.append(subfield['code'])
                subfields_700.append(subfield.text)
            recent_record.add_field(Field(tag='700', indicators=[responsible['ind1'], responsible['ind2']], subfields=subfields_700))
    nonfiling_characters = '0'
    if language in language_articles.keys():
        first_word=(xml_soup.find('datafield', tag='245').find('subfield', code='a').text).split()[0].lower()
        if first_word in language_articles[language]:
            nonfiling_characters=str(len(first_word)+1)
    subfields_245 = []
    for subfield in xml_soup.find('datafield', tag='245').find_all('subfield'):
        subfields_245.append(subfield['code'])
        subfields_245.append(xml_soup.find('datafield', tag='245').find('subfield', code=subfield['code']).text)
    recent_record.add_field(Field(tag='245', indicators=[ind_1_245, nonfiling_characters], subfields=subfields_245))
    recent_record.add_field(Field(tag='264', indicators=[' ', '1'], subfields=['a', 'Chicago', 'b', 'The Oriental Institute', 'c', year]))
    for pdf in pdfs:
        recent_record.add_field(Field(tag='856', indicators=['4', '1'], subfields=['z', 'application/pdf', 'u', pdf]))
    recent_record.add_field(Field(tag='856', indicators=['4', '1'],
                                  subfields=['z', 'Abstract', 'u', url]))
    out.write(recent_record.as_marc21())

out=open('oi_all.mrc', 'wb')
basic_url = 'https://oi.uchicago.edu/research/publications/archaeology'
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
    oi_page = response.read()
oi_page = oi_page.decode('utf-8')
oi_soup = BeautifulSoup(oi_page, 'html.parser')
oi_lis = oi_soup.find_all('li')
oi_pubs = []
for li in oi_lis:
    for a in li.find_all('a'):
        if 'research/publications' in a['href']:
            href=a['href']
            oi_pubs.append(href)
oi_pubs = oi_pubs[6:]
pubs_already_checked=[]
begin=False
list_of_files = os.listdir('oi_c')
for pub in oi_pubs:
    record_nr+=1
    print(record_nr)
    if pub in pubs_already_checked:
        continue
    else:
        pubs_already_checked.append(pub)
        url = "https://oi.uchicago.edu"+pub
        print(url)
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
        values = {'name': 'Helena Nebel',
                  'location': 'Berlin',
                  'language': 'Python'}
        headers = {'User-Agent': user_agent}
        data = urllib.parse.urlencode(values)
        data = data.encode('ascii')
        req = urllib.request.Request(url, data, headers)
        with urllib.request.urlopen(req) as response:
            journal_page = response.read()
        journal_page = journal_page.decode('utf-8')
        journal_soup = BeautifulSoup(journal_page, 'html.parser')
        title=journal_soup.find('article').find('h1').text
        pdfs=[]
        for item in journal_soup.find_all('a', text='Download'):
            if '.pdf' in item['href']:
                pdfs.append('https://oi.uchicago.edu'+item['href'])
        print(title)

        with open('oi_c/'+str(record_nr)+'.xml', 'r') as xml_file:
            xml_soup=BeautifulSoup(xml_file, 'xml')
            create_new_record(out, xml_soup, pdfs, url, record_nr)

