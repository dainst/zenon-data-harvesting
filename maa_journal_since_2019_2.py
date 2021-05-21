import urllib.parse, urllib.request
from pymarc import Record, Field
import arrow
import language_codes
from bs4 import BeautifulSoup
import os
from pdf2image import convert_from_path
import tempfile
from nltk.tokenize import RegexpTokenizer, word_tokenize
import ast
import re
from nameparser import HumanName
from langdetect import detect
import spacy
from scipy import spatial
import unicodedata
from nltk.corpus import stopwords
import itertools
import json

stopwords_de=stopwords.words('german')
stopwords_en=stopwords.words('english')
stopwords_fr=stopwords.words('french')
stopwords_es=stopwords.words('spanish')
stopwords_it=stopwords.words('italian')
stopwords_nl=stopwords.words('dutch')

def remove_accents(word_list):
    new_word_list=[]
    for word in word_list:
        nfkd_form = unicodedata.normalize('NFKD', word)
        new_word_list.append(nfkd_form.encode('ASCII', 'ignore').decode('ascii'))
    return new_word_list

nlp_de = spacy.load('de_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')
nlp_fr = spacy.load('fr_core_news_sm')
nlp_es = spacy.load('es_core_news_sm')
nlp_it = spacy.load('it_core_news_sm')
nlp_nl = spacy.load('nl_core_news_sm')
nlp_xx = spacy.load('xx_ent_wiki_sm')

language_articles = {'eng': ['the', 'a', 'an'], 'fre': ['la', 'le', 'les', 'un', 'une', 'l\'', 'il'],
                     'spa': ['el', 'lo', 'la', 'las', 'los',
                             'uno' 'un', 'unos', 'unas', 'una'], 'ger': ['das', 'der', 'ein', 'eine', 'die'],
                     'ita': ['gli', 'i', 'le', 'la', 'l\'',
                             'lo', 'il', 'gl\'', 'l']}
sysnumbers_file = open('maa_volumes_sysnumbers.json', 'r')
volumes_sysnumbers = json.load(sysnumbers_file)
sysnumbers_file.close()

def doi_is_valid(doi):
    try:
        req = urllib.request.Request(doi)
        with urllib.request.urlopen(req) as response:
            doi_page = response.read()
        return True
    except:
        return False

def create_245_and_246(recent_record, title, nonfiling_characters, author_nr):
    if len(title.split(". "))>1:
        recent_record.add_field(Field(tag='245', indicators=[str(author_nr), nonfiling_characters], subfields=['a', title.split(". ", 1)[0], 'b', title.split(". ", 1)[1]]))
    else:
        recent_record.add_field(Field(tag='245', indicators=[str(author_nr), nonfiling_characters], subfields=['a', title]))

def determine_nonfiling_characters(recent_record, title, year):
    time_str = arrow.now().format('YYMMDD')
    nonfiling_characters = 0
    language = language_codes.resolve(detect(title))
    recent_record.add_field(Field(tag='041', indicators=['1', ' '], subfields=['a', language]))
    if language in language_articles.keys():
        first_word = (title.split()[0]).lower()
        if first_word in language_articles[language]:
            nonfiling_characters = str(len(first_word) + 1)
    data_008 = str(time_str) + 's' + year + '    ' + 'gr ' + '|||| |     |    |' + language + ' d'
    recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
    return nonfiling_characters

def create_new_record(adjusted_parts_of_title, out, toc, pdf, pages, issue, year, titles_processed):
    recent_record = Record(force_utf8=True)
    if "DOI:" in adjusted_parts_of_title[-1]:
        possible_doi = "https://www.doi.org/"+(adjusted_parts_of_title[-1].replace("DOI:", "").strip())
        if doi_is_valid(possible_doi)==True:
            doi=possible_doi
            recent_record.add_field(Field(tag='024', indicators=['7', ' '], subfields=['a', doi, '2', 'doi', 'q', 'pdf']))
        del adjusted_parts_of_title[-1]
    authors=[]
    adjusted_parts_of_title[0] =adjusted_parts_of_title[0]
    if len(adjusted_parts_of_title)==3:
        adjusted_parts_of_title = adjusted_parts_of_title[:-1]
    for entry in adjusted_parts_of_title:
        if len(re.findall(r'[a-z]', entry))>=3 and len(re.findall(r'[A-Z]{4}', entry))==0 and adjusted_parts_of_title.index(entry)==1:
            if len(entry.split(','))>=len(entry.split()):
                all_names = entry.split(", ")
                authors = [all_names[all_names.index(author)+1]+" "+author for author in all_names if all_names.index(author)%2==0]
            else:
                authors = entry.split(", ")
    authors = [author.strip('\t').strip().strip('\t').strip() for author in authors]
    authors = [re.sub(r'[0-9]', '', aut) for author in authors for aut in author.split(' and ')]
    authors = [HumanName(author).last + ", " + HumanName(author).first for author in authors]
    authors = [author+"." if len(re.findall(r'[A-Z]', author[-1]))>0 else author for author in authors]
    author_nr = 0
    for author in authors:
        if author_nr == 0:
            recent_record.add_field(Field(tag='100', indicators=['1', ' '], subfields=['a', author]))
            author_nr += 1
        else:
            recent_record.add_field(Field(tag='700', indicators=['1', ' '], subfields=['a', author]))
            author_nr = author_nr
    title=adjusted_parts_of_title[0]
    title_word_list = RegexpTokenizer(r'\w+').tokenize(title)
    title_word_list.sort(key=len, reverse=True)
    for word in title_word_list:
        for item in re.findall(r'(?:^|\W)'+ word + r'(?:\W|$)', title):
            if item[0] == "'" and len(item) == 3:
                title=title.replace(item, item.replace(word, word.lower()))
            else:
                title=title.replace(item, item.replace(word, word.capitalize()))
    if title not in titles_processed:
        recent_record.add_field(Field(tag='006', indicators=None, data='|||| |     |    |'))
        recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'ta'))
        recent_record.add_field(Field(tag='040', indicators=[' ', ' '], subfields=['a', 'MAA', 'd', 'DE-2553']))
        recent_record.add_field(Field(tag='336', indicators=[' ', ' '], subfields=['a', 'text', 'b', 'txt', '2', 'rdacontent']))
        recent_record.add_field(Field(tag='337', indicators=[' ', ' '], subfields=['a', 'unmediated', 'b', 'n', '2', 'rdamedia']))
        recent_record.add_field(Field(tag='338', indicators=[' ', ' '], subfields=['a', 'volume', 'b', 'nc', '2', 'rdacarrier']))
        recent_record.leader = recent_record.leader[:5] + 'nab a       uu ' + recent_record.leader[20:]
        recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'arom']))
        recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', '2019xhnxmaa']))
        nonfiling_characters = determine_nonfiling_characters(recent_record, title, year)
        create_245_and_246(recent_record, title, nonfiling_characters, author_nr)
        titles_processed.append(title)
        recent_record.add_field(Field(tag='264', indicators=[' ', '1'], subfields=['a', 'Rhodes', 'b', 'University of the Aegean', 'c', year]))
        recent_record.add_field(Field(tag='856', indicators=['4', '2'],
                                      subfields=['z', 'Table of Contents', 'u', toc]))
        recent_record.add_field(Field(tag='LKR', indicators=[' ', ' '],
                                      subfields=['a', 'ANA', 'b', volumes_sysnumbers[year], 'l', 'DAI01',
                                                 'm', title, 'n', 'Mediterranean Archaeology & Archaeometry, ' +volume+" ("+year+")", 'x', '2241-8121']))
        recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', 'Fasc.'+issue_nr]))
        #print(recent_record)
        out.write(recent_record.as_marc21())
    return titles_processed

titles_processed=[]
issue_data={}
out = None
basic_url = 'http://www.maajournal.com/'
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
    journal_page = response.read()
journal_page = journal_page.decode('utf-8')
journal_soup = BeautifulSoup(journal_page, 'html.parser')
issues = journal_soup.find_all('div', class_='wifeo_pagesousmenu')
issues_per_year=[]
system_nrs = {}
for issue in issues:
    url = basic_url+issue.find('a')['href']+'#mw999'
    if url=="http://www.maajournal.com/Issues2019a.php#mw999":
        continue
    toc = url
    year=re.findall('\d{4}', issue.find('a')['href'])[0]
    if year < '2019':
        break
    if year not in volumes_sysnumbers:
        volumes_sysnumbers[year]=input("Bitte geben Sie eine gültige Systemnummer ein: ")
    req = urllib.request.Request(url, data, headers)
    with urllib.request.urlopen(req) as response:
        issue_page = response.read()
    issue_soup = BeautifulSoup(issue_page, 'html.parser')
    issue_nr=issue_soup.find('title').text.split("Issue ")[-1]
    issue_nr=re.sub(r' \([^)]*\)', '', issue_nr)
    if len(issues_per_year)!=0:
        if issue_nr+"_"+year != issues_per_year[-1]:
            issues_per_year.append(issue_nr)
        else:
            issues_per_year.append(issue_nr)
    volume=issue_soup.find('title').text.split(" - ")[0].replace("Volume ", "")
    if year+"_"+volume not in issue_data.keys():
        issue_data[year+"_"+volume]={}
    issue_file_name = year + "_" + issue_nr
    if issue_file_name not in issues:
        out = open("maa/"+issue_file_name+"_new.mrc", 'wb')
    article_nr = 0
    article_info_and_pdf=issue_soup.find_all('p', class_='style9 style12')
    article_info_and_pdf=[item.find('span', class_='style18') for item in article_info_and_pdf if item.find('span', class_='style18') is not None]
    lines_printed=0
    for item in article_info_and_pdf:
        pages=None
        pdf=None
        adjusted_parts_of_title=[part.strip() for part in item.text.split('\n')]
        create_new_record(adjusted_parts_of_title, out, toc, pdf, pages, issue, year, titles_processed)

sysnumbers_file = open('maa_volumes_sysnumbers.json', 'w')
json.dump(volumes_sysnumbers, sysnumbers_file)
sysnumbers_file.close()