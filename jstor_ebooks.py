import urllib.parse, urllib.request
from pymarc import Record, Field, MARCReader
import arrow
import language_codes
#import nltk
from nltk.tokenize import RegexpTokenizer
from bs4 import BeautifulSoup
import ast
import spacy
from langdetect import detect
from nameparser import HumanName
import re
import os
#from langdetect import detect_langs
#import polyglot
#from polyglot.text import Text, Word
nlp_de = spacy.load('de_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')
nlp_fr = spacy.load('fr_core_news_sm')
nlp_es = spacy.load('es_core_news_sm')
nlp_it = spacy.load('it_core_news_sm')
nlp_nl = spacy.load('nl_core_news_sm')
nlp_xx = spacy.load('xx_ent_wiki_sm')

language_articles={'eng': ['the','a', 'an'], 'fre':['la','le','les','un', 'une', 'l\'', 'il'], 'spa':['el','lo','la','las','los',
'uno' 'un', 'unos', 'unas', 'una'], 'ger':['das', 'der', 'ein', 'eine', 'die'], 'ita':['gli', 'i','le', 'la', 'l\'',
'lo', 'il', 'gl\'', 'l']}


def swagger_search_ebook(search_title, search_authors, year, title):
    selected_sysnumber=None
    url=u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0[]='+search_authors+'&type0[]=Author&lookfor0[]='+search_title+'&type0[]=Title&lookfor0[]=Available+online+for+registered+users+of+FID&type0[]=AllFields&bool0[]=AND&illustration=-1&daterange[]=publishDate&publishDatefrom=&publishDateto='
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        journal_page = response.read()
    journal_page=journal_page.decode('utf-8')
    resultcount=str(ast.literal_eval(str(journal_page))["resultCount"])
    if resultcount>'0':
        for entry in ast.literal_eval(str(journal_page))["records"]:
            if "[Rez.zu]" not in entry["title"]:
                sysnumber=entry["id"]
                print(sysnumber, "als Ebook vorhanden")
                continue
    if resultcount=='0':
        url=u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0[]='+search_authors+'&type0[]=Author&lookfor0[]='+search_title+'&type0[]=Title&bool0[]=AND&illustration=-1&daterange[]=publishDate&publishDatefrom=&publishDateto='
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            journal_page = response.read()
        journal_page=journal_page.decode('utf-8')
        resultcount=str(ast.literal_eval(str(journal_page))["resultCount"])
        if resultcount>'0':
            for entry in ast.literal_eval(str(journal_page))["records"]:
                if "[Rez.zu]" not in entry["title"]:
                    print(entry["title"])
                    sysnumber=entry["id"]
                    print(sysnumber)
            inputstring=input("Welchen Record wollen Sie verwenden?")
            if inputstring!="k":
                selected_sysnumber=inputstring
        if resultcount=='0':
            if len(search_authors.rsplit("+", 1))>=2:
                adjusted_search_authors=search_authors.rsplit("+", 1)[1]
            else:
                adjusted_search_authors=search_authors
            url=u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0[]='+adjusted_search_authors+'&type0[]=Author&lookfor0[]='+search_title+'&type0[]=Title&type0[]=AllFields&bool0[]=AND&illustration=-1&daterange[]=publishDate&publishDatefrom=&publishDateto='
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                journal_page = response.read()
            journal_page=journal_page.decode('utf-8')
            resultcount=str(ast.literal_eval(str(journal_page))["resultCount"])
            if resultcount>'0':
                for entry in ast.literal_eval(str(journal_page))["records"]:
                    if "[Rez.zu]" not in entry["title"]:
                        print(entry["title"])
                        sysnumber=entry["id"]
                inputstring=input("Welchen Record wollen Sie verwenden?")
                if inputstring!="k":
                    selected_sysnumber=inputstring
    if resultcount=='0':
        print("\033[45m"+title+"\033[0m")
    return selected_sysnumber
#definition für create_review_title

def create_new_record(recent_record, out, link, year, href):
        time_str=arrow.now().format('YYMMDD')
        data_008=str(time_str)+'s'+ year + '    ' + 'enk' + ' |   o     |    |' + 'eng'  +' d'
        recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
        recent_record.add_field(Field(tag='006', indicators=None, subfields=None, data=u'm        d        '))
        recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'tc'))
        recent_record.add_field(Field(tag='041', indicators = ['1', ' '], subfields = ['a', 'eng']))
        recent_record.add_field(Field(tag='336', indicators = [' ', ' '], subfields = ['a', 'text', 'b', 'txt', '2', 'rdacontent']))
        recent_record.add_field(Field(tag='337', indicators = [' ', ' '], subfields = ['a', 'computer', 'b', 'c', '2', 'rdamedia']))
        recent_record.add_field(Field(tag='336', indicators = [' ', ' '], subfields = ['a', 'online resource', 'b', 'cr', '2', 'rdacarrier']))
        recent_record.add_field(Field(tag='040', indicators = [' ', ' '], subfields = ['a', 'FID-ALT-KA-DE-16', 'd', 'DE-2553']))
        recent_record.leader = recent_record.leader[:5] + 'nmm a       uu ' + recent_record.leader[20:]
        recent_record.add_field(Field(tag='300', indicators = [' ', ' '], subfields = ['a', '1 online resource']))
        recent_record.add_field(Field(tag='500', indicators = [' ', ' '], subfields = ['a', 'Fachinformationsdienst Altertumswissenschaften (FID) Propylaeum: Sie können auf dieses Volltext-Angebot zugreifen, \
sofern Sie sich registriert haben und zum berechtigten Nutzerkreis gehören. Weitere Informationen finden Sie hier: https://www.propylaeum.de/service/fid-lizenzen/']))
        recent_record.add_field(Field(tag='500', indicators = [' ', ' '], subfields = ['a', 'Propylaeum – Fachinformationsdienst Altertumswissenschaften ist der, gemeinsam von der Bayerischen Staatsbibliothek München und der Universitätsbibliothek Heidelberg, betriebene Fachinformationsdienst Altertumswissenschaften. Im Kontext der aktuellen Förderung durch die DFG sorgt Propylaeum mit Hilfe sogenannter „FID-Lizenzen“ auch für die überregionale Bereitstellung lizenzpflichtiger digitaler Medien.']))
        recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', '2019xhnxjsotreeb']))
        recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'online publication']))
        recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'jstorebclassstud']))
        if input("Wollen Sie die Erscheinungsdaten übernehmen?")!="y":
            place_of_publication=input("Bitte geben Sie den Verlagsort an: ")
            publisher=input("Bitte geben Sie den Verlag an: ")
            if recent_record['264']!=None:
                recent_record['264']['a']=place_of_publication
                recent_record['264']['b']=publisher
                recent_record['264']['c']=year
            else:
                recent_record.remove_fields('260')
                recent_record.add_field(Field(tag='264', indicators = [' ', '1'],
                                              subfields = ['a', place_of_publication, 'b', publisher, 'c', year]))
        else:
            if recent_record['264']==None:
                recent_record.add_field(Field(tag='264', indicators = [' ', '1'],
                                              subfields = ['a', recent_record['260']['a'], 'b', recent_record['260']['b'], 'c', year]))
                recent_record.remove_fields('260')
        recent_record.add_field(Field(tag='856', indicators = ['4', '0'],
                                          subfields = ['z', 'Available online for registered users of FID', 'u', href]))
        toc=href.replace("http://proxy.fid-lizenzen.de/han/jstor-ebooks-altertum/", "https://")
        recent_record.add_field(Field(tag='856', indicators = ['4', '1'],
                                      subfields = ['z', 'Table of Contents', 'u', toc]))
        out.write(recent_record.as_marc21())
        return recent_record

out=open('jstor.mrc', 'wb')
record_nr=0
url='https://altertum.fid-lizenzen.de/angebote/nlproduct.2019-02-05.2319777124'
user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
values = {'name': 'Helena Nebel',
          'location': 'Berlin',
          'language': 'Python' }
headers = {'User-Agent': user_agent}
data = urllib.parse.urlencode(values)
data = data.encode('ascii')
req = urllib.request.Request(url, data, headers)
with urllib.request.urlopen(req) as response:
    page = response.read()
page=page.decode('utf-8')
soup=BeautifulSoup(page, 'html.parser')
links=soup.find_all("td")
linklist=[]
hreflist=[]
for link in links:
    if link.find("a")!=None:
        linklist.append(link.find("a").text)
        hreflist.append(link.find("a")['href'])
linklist=linklist[4:]
hreflist=hreflist[4:]
link_nr=0
for link in linklist:
    href=hreflist[linklist.index(link)]
    link_nr+=1
    remove_parentheses = re.compile(".*?\((.*?)\)")
    result = re.findall(remove_parentheses, link)
    for item in result:
        link=link.replace(" ("+item+")", "")
    year=result[-1][-4:]
    print()
    print(link)
    author_names=[]
    if (" : " in link) and (", " in link.split(" : ", 1)[0]):
        title=link.split(" : ", 1)[1]
        author_names=link.split(" : ", 1)[0].split('; ')
    else:
        title=link
    #print(title)
    search_title=""
    word_nr=0
    search_authors=""
    name_nr=0
    for author_name in author_names:
        name_nr+=1
        if name_nr<=1:
            name=urllib.parse.quote(author_name.split(", ")[0], safe='')
            if ("." not in name):
                search_authors=search_authors+"+"+name
    search_authors=search_authors.strip("+")
    for word in RegexpTokenizer(r'\w+').tokenize(title):
        if (word_nr<7) and (len(word)>3):
            word=urllib.parse.quote(word, safe='')
            search_title=search_title+"+"+word
            word_nr+=1
    search_title=search_title.strip("+")
    selected_sysnumber=swagger_search_ebook(search_title, search_authors, year, title)
    if selected_sysnumber!=None:
        print(selected_sysnumber, "ausgewählt.")
        webFile = urllib.request.urlopen("https://zenon.dainst.org/Record/"+selected_sysnumber+"/Export?style=MARC")
        marcFile = open('records/jstor/jstor'+str(link_nr)+'.mrc', 'wb')
        marcFile.write(webFile.read())
        marcFile.close()
        webFile.close()
        with open('records/jstor/jstor'+str(link_nr)+'.mrc', 'rb') as selected_record:
            reader = MARCReader(selected_record)
            recent_record = next(reader)
            recent_record.remove_fields('001', '005', '003', '008', '010', '015', '020', '336', '337', '338', '993', '504', '490', '300', '035', '590', '040')
            recent_record=create_new_record(recent_record, out, link, year, href)



