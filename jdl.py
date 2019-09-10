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
import json
import urllib.parse, urllib.request
from pymarc import Record, Field
import arrow
import language_codes
from bs4 import BeautifulSoup
import os
from pdf2image import convert_from_path
import tempfile
import ast
import re
from nameparser import HumanName
from langdetect import detect
import spacy
from scipy import spatial
import unicodedata
from nltk.corpus import stopwords
import itertools
from pymarc import MARCReader
import urllib.parse, urllib.request
import ast
from nltk.tokenize import RegexpTokenizer
import json

stopwords_de=stopwords.words('german')
stopwords_en=stopwords.words('english')
stopwords_fr=stopwords.words('french')
stopwords_es=stopwords.words('spanish')
stopwords_it=stopwords.words('italian')
stopwords_nl=stopwords.words('dutch')

authors_file = open('authors_file.txt', 'w')

language_articles = {'eng': ['the', 'a', 'an'], 'fre': ['la', 'le', 'les', 'un', 'une', 'l\'', 'il'],
                     'spa': ['el', 'lo', 'la', 'las', 'los',
                             'uno' 'un', 'unos', 'unas', 'una'], 'ger': ['das', 'der', 'ein', 'eine', 'die'],
                     'ita': ['gli', 'i', 'le', 'la', 'l\'',
                             'lo', 'il', 'gl\'', 'l']}

def lower_list(list):
    list=[word.lower() for word in list]
    return list

def calculate_cosine_similarity(title, found_title):
    title_list=RegexpTokenizer(r'\w+').tokenize(title)
    found_title_list=RegexpTokenizer(r'\w+').tokenize(found_title)
    [title_list, found_title_list] = [lower_list(a) for a in [title_list, found_title_list]]
    [title_list, found_title_list] = [remove_accents(word) for word in [title_list, found_title_list]]
    if len(title_list)>len(found_title_list):
        title_list_count=[title_list.count(word) for word in title_list if (word not in stopwords_de)]
        found_title_list_count=[found_title_list.count(word) for word in title_list if (word not in stopwords_de)]
    else:
        title_list_count=[title_list.count(word) for word in found_title_list if (word not in stopwords_de)]
        found_title_list_count=[found_title_list.count(word) for word in found_title_list if (word not in stopwords_de)]
    similarity = 1 - spatial.distance.cosine(title_list_count, found_title_list_count)
    #print(similarity)
    if similarity>0.9:
        return True
    elif similarity>0.68:
        skipped_word_nr=0
        skipped=False
        mismatches_nr=0
        matches_nr=0
        for word in title_list:
            if skipped_word_nr>(len(title_list)/3):
                return False
            if word in found_title_list:
                if any(index == found_title_list.index(word) for index in [title_list.index(word)+1+skipped_word_nr, title_list.index(word)+skipped_word_nr, title_list.index(word)-1+skipped_word_nr]):
                    if word not in stopwords_de:
                        matches_nr+=1
                else:
                    if word not in stopwords_de:
                        mismatches_nr+=1
            else:
                skipped_word_nr+=1
        #print(matches_nr, mismatches_nr)
        if (matches_nr > mismatches_nr*2):
            return True
    return False

def swagger_find_article(search_title, search_authors, year, title):
    if search_authors!="":
        url=u'https://zenon.dainst.org/api/v1/search?lookfor=title%3A'+search_title+'%20AND%20author%3A'+search_authors+'%20AND%20publishDate%3A'+year+'&type=AllFields&sort=relevance&page=1&limit=20&prettyPrint=false&lng=de'
    else:
        url=u'https://zenon.dainst.org/api/v1/search?lookfor=title%3A'+search_title+'%20AND%20publishDate%3A'+year+'&type=AllFields&sort=relevance&page=1&limit=20&prettyPrint=false&lng=de'
    #print(url)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        journal_page = response.read()
    journal_page=journal_page.decode('utf-8')
    resultcount=str(ast.literal_eval(str(journal_page))["resultCount"])
    right_result = False
    ancestorid = ""
    if resultcount>='1':
        for found_record in ast.literal_eval(str(journal_page))["records"]:
            title_found=found_record["title"]
            sysnr = found_record["id"]
            similarity = calculate_cosine_similarity(title, title_found)
            if similarity==False:
                resultcount = '0'
            if similarity==True:
                webFile = urllib.request.urlopen("https://zenon.dainst.org/Record/"+found_record['id']+"/Export?style=MARC")
                new_reader = MARCReader(webFile)
                for file in new_reader:
                    if file['995']!=None:
                        parentid = file['995']['b']
                        webFile = urllib.request.urlopen("https://zenon.dainst.org/Record/"+parentid+"/Export?style=MARC")
                        parent_reader = MARCReader(webFile)
                        for parent_file in parent_reader:
                            if parent_file['995']!=None:
                                print('ancestor:', parent_file['995']['n'])
                                ancestorid = parent_file['995']['b']
                                print('ancestorid:', ancestorid)
            if ancestorid == '000035916':
                resultcount = '1'
            else:
                resultcount = '0'
            if resultcount=='1':
                break
    return resultcount

def find_article(title, authors, year):
    resultcount='0'
    search_title=""
    search_authors=""
    word_nr=0
    author_nr=0
    for author in authors:
        name = author.split(", ")[0]
        if author_nr<2:
            name=urllib.parse.quote(name, safe='')
            if ("." not in name):
                search_authors=search_authors+"+"+name
        author_nr += 1
    search_authors=search_authors.strip("+")
    nfkd_form = unicodedata.normalize('NFKD', title)
    title = nfkd_form.encode('ASCII', 'ignore').decode('ascii')
    title = title.replace("...", " ")
    for word in RegexpTokenizer(r'\w+').tokenize(title):
        if (not 'vol' in word.lower()) and (word_nr<7) and (len(word)>2) and (word not in stopwords_de):
            word=urllib.parse.quote(word, safe='')
            search_title=search_title+"+"+word
            word_nr+=1
        if word_nr>=2:
            search_title=search_title.strip("+")
            resultcount=swagger_find_article(search_title, search_authors, year, title)
        if resultcount=='0':
            search_authors=search_authors.split("+")[0]
            resultcount=swagger_find_article(search_title, search_authors, year, title)
        if resultcount=='0':
            resultcount=swagger_find_article(search_title, "", year, title)
        if resultcount=='0':
            search_title=""
            word_nr=0
            adjusted_title=title.split(".")[0].split(":")[0]
            for word in RegexpTokenizer(r'\w+').tokenize(adjusted_title):
                if (not 'vol' in word.lower()) and (word_nr<8) and (len(word)>3):
                    word=urllib.parse.quote(word, safe='')
                    if '%' in word:
                        continue
                    search_title=search_title+"+"+word
                    word_nr+=1
            search_title=search_title.strip("+")
            resultcount=swagger_find_article(search_title, search_authors, year, title)
        if resultcount=='0':
            search_authors=""
            resultcount=swagger_find_article(search_title, search_authors, year, title)
        if resultcount=='0':
            if len(RegexpTokenizer(r'\w+').tokenize(title))>4:
                for pair in itertools.combinations(search_title.split("+"), 2):
                    search_title_without_words=search_title
                    if resultcount>'0':
                        break
                    for word in pair:
                        search_title_without_words=search_title_without_words.replace(word, '').replace('++', '+').strip('+')
                    resultcount=swagger_find_article(search_title_without_words, search_authors, year, title)
            else:
                for word in search_title.split("+"):
                    search_title_without_words=search_title
                    if resultcount>'0':
                        break
                    search_title_without_words=search_title_without_words.replace(word, '').replace('++', '+').strip('+')
                    resultcount=swagger_find_article(search_title_without_words, search_authors, year, title)
        return resultcount

def remove_accents(word_list):
    new_word_list=[]
    for word in word_list:
        nfkd_form = unicodedata.normalize('NFKD', word)
        new_word_list.append(nfkd_form.encode('ASCII', 'ignore').decode('ascii'))
    return new_word_list

def create_245_and_246(recent_record, title, nonfiling_characters, author_nr):
    recent_record.add_field(Field(tag='245', indicators=[str(author_nr), nonfiling_characters], subfields=['a', title]))

def determine_nonfiling_characters(recent_record, title, date_of_publication, language):
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

def create_new_record(item, out, volume_url, volume_year, date_published_online, date_of_publication, all_authors, volume):
    doi=None
    recent_record = Record(force_utf8=True)
    recent_record.add_field(
        Field(tag='336', indicators=[' ', ' '], subfields=['a', 'text', 'b', 'txt', '2', 'rdacontent']))
    recent_record.add_field(
        Field(tag='337', indicators=[' ', ' '], subfields=['a', 'computer', 'b', 'c', '2', 'rdamedia']))
    recent_record.add_field(
        Field(tag='338', indicators=[' ', ' '], subfields=['a', 'online resource', 'b', 'cr', '2', 'rdacarrier']))
    title=item.find('mods:title').text
    authors = []
    author_nr = 0
    for author in item.find_all('mods:name'):
        author_name = ""
        if author.find_all('mods:roleTerm')!=[]:
            if author_name==author.find('mods:displayForm').text:
                continue
            author_name = author.find('mods:displayForm').text
            authors.append(author_name)
            if author_nr == 0:
                recent_record.add_field(Field(tag='100', indicators=['1', ' '], subfields=['a', author_name]))
                author_nr += 1
            else:
                recent_record.add_field(Field(tag='700', indicators=['1', ' '], subfields=['a', author_name]))
                author_nr = author_nr
    resultcount = find_article(title, authors, date_of_publication)
    if resultcount == '1':
        print(title)
    if resultcount == '0':
        physical_info = item.find('mods:physicalDescription')
        recent_record.add_field(Field(tag='006', indicators=None, data='m        d        '))
        recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data='cr  uuu    a uuuuu'))
        if physical_info!=None:
            if physical_info.find('mods:extent', unit='pages')!=None:
                pages = physical_info.find('mods:extent', unit='pages').text
                recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', pages]))
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
        #print(recent_record)
        out.write(recent_record.as_marc21())

out=None
time_str = arrow.now().format('YYMMDD')
basic_url = 'https://digi.ub.uni-heidelberg.de/diglit/jdi'
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
all_authors=[]
for volume_url in volume_urls:
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
    volume_year=volume_years[record_nr].split('(')[0]
    mets_url=volume_url.split("?")[0]+'/mets'
    webFile = urllib.request.urlopen(mets_url)
    xml_soup=BeautifulSoup(webFile, 'xml')
    record_nr+=1
    if volume_url not in volumes_already_processed:
        volumes_already_processed.append(volume_url)
        out = open('records/JdI/JdI' + volume_year.split('/')[0] + '.mrc', 'wb')
    else:
        out = out
    date_of_publication = xml_soup.find_all('mods:mods')[0].find('mods:originInfo').find('mods:dateIssued', keyDate='yes').text
    if '(' in date_of_publication:
        date_of_publication = date_of_publication.split('(')[1].replace(')')
    volume=xml_soup.find_all('mods:mods')[0].find('mods:number').text
    for item in xml_soup.find_all('mods:mods')[1:]:
        create_new_record(item, out, volume_url, volume_year, date_published_online, date_of_publication, all_authors, volume)