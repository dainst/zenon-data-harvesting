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

def create_new_record(out, xml_soup, pdfs, url, record_nr):
    time_str = arrow.now().format('YYMMDD')
    recent_record = Record(force_utf8=True)
    #print(xml_soup)
    if xml_soup.find('datafield', tag='245').find('b')!=None:
        title_for_lang_detection=xml_soup.find('datafield', tag='245').find('subfield', code='a').text+" "+xml_soup.find('datafield', tag='245').find('subfield', code='b').text
    else:
        title_for_lang_detection=xml_soup.find('datafield', tag='245').find('subfield', code='a').text
    language = language_codes.resolve(detect(title_for_lang_detection))
    recent_record.add_field(Field(tag='006', indicators=None, data='m        d        '))
    recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'tz'))
    old_008 = xml_soup.find('controlfield', tag='008').text
    print(old_008)
    year='    '
    copyright_year=''
    if len(xml_soup.find_all('datafield', tag='260'))!=0:
        year=re.findall(r'(\d{4})',xml_soup.find_all('datafield', tag='260')[0].find('subfield', code='c').text)[0]
    if len(xml_soup.find_all('datafield', tag='264'))==0:
        copyright_year=input('Bitte geben Sie das Copyright-Jahr an: ')
    if len(xml_soup.find_all('datafield', tag='264'))==1:
        year=re.findall(r'(\d{4})',xml_soup.find_all('datafield', tag='264')[0].find('subfield', code='c').text)[0]
    if len(xml_soup.find_all('datafield', tag='264'))==2:
        year=re.findall(r'\d{4}',xml_soup.find_all('datafield', tag='264')[0].find('subfield', code='c').text)[0]
        copyright_year=re.findall(r'\d{4}',xml_soup.find_all('datafield', tag='264')[1].find('subfield', code='c').text)[0]
    if copyright_year=='':
        data_008 = time_str+'s'+year+'    '+'ilu'+' |   o     |    |'+old_008[-5:]
    else:
        data_008 = time_str+'t'+year+copyright_year+'ilu'+' |   o     |    |'+old_008[-5:]
    print(data_008)
    #str(time_str) + 's' + year + '    ' + 'gr ' + ' |   o     |    |' + language + ' d'
    '''
    data_008 = str(time_str) + 's' + year + '    ' + 'gr ' + ' |   o     |    |' + language + ' d'
    

    recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
    recent_record.add_field(Field(tag='040', indicators=[' ', ' '], subfields=['a', 'DE-2553', 'b', 'DE-2553']))
    recent_record.add_field(Field(tag='336', indicators=[' ', ' '], subfields=['a', 'text', 'b', 'txt', '2', 'rdacontent']))
    recent_record.add_field(Field(tag='337', indicators=[' ', ' '], subfields=['a', 'computer', 'b', 'c', '2', 'rdamedia']))
    recent_record.add_field(Field(tag='338', indicators=[' ', ' '], subfields=['a', 'online resource', 'b', 'cr', '2', 'rdacarrier']))
    recent_record.leader = recent_record.leader[:5] + 'mmb a       uu ' + recent_record.leader[20:]
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'arom']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', '2019xhnxmaa']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'online publication']))
    recent_record.add_field(Field(tag='041', indicators=['1', ' '], subfields=['a', language]))

    recent_record.add_field(Field(tag='245', indicators=[str(author_nr), nonfiling_characters], subfields=['a', title]))

    recent_record.add_field(Field(tag='264', indicators=[' ', '1'], subfields=['a', 'Rhodes', 'b', 'University of the Aegean', 'c', year]))
    for pdf in pdfs:
        recent_record.add_field(Field(tag='856', indicators=['4', '1'], subfields=['z', 'application/pdf', 'u', pdf]))
    recent_record.add_field(Field(tag='856', indicators=['4', '1'],
                                  subfields=['z', 'Abstract', 'u', url]))
    out.write(recent_record.as_marc21())'''

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
        previous_title=title
        title=urllib.parse.quote(title, safe='')
        pdfs=[]
        for item in journal_soup.find_all('a', text='Download'):
            if '.pdf' in item['href']:
                pdfs.append(item['href'])
        print(previous_title)
        number=input('Bitte geben sie die ID ein: ')
        with open('oi_c/'+str(record_nr)+'.xml', 'r') as xml_file:
            xml_soup=BeautifulSoup(xml_file, 'xml')
            create_new_record(out, xml_soup, pdfs, url, record_nr)
