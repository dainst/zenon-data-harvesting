import urllib.parse, urllib.request
from pymarc import Record, Field
import arrow
import language_codes
#import nltk
from nltk.tokenize import RegexpTokenizer
from bs4 import BeautifulSoup
import ast
import spacy
from langdetect import detect
from nameparser import HumanName
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

def swagger_search_ebook(search_title, search_authors, recent_record, year, title):
    search_review=search_title+"+"+search_authors
    ebook=False
    resultcount_review='0'
    url=u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0[]='+search_authors+'&type0[]=Author&lookfor0[]='+search_title+'&type0[]=Title&lookfor0[]=Oxford+Scholarship+Online&type0[]=AllFields&bool0[]=AND&illustration=-1&daterange[]=publishDate&publishDatefrom=&publishDateto='
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        journal_page = response.read()
    journal_page=journal_page.decode('utf-8')
    resultcount=str(ast.literal_eval(str(journal_page))["resultCount"])
    if resultcount>'0':
        for entry in ast.literal_eval(str(journal_page))["records"]:
            if "[Rez.zu]" not in entry["title"]:
                print(entry["title"])
                ebook=True
                sysnumber=str(ast.literal_eval(str(journal_page))["records"][0]["id"])
                print('Kein Datensatz erstellt, unter', sysnumber, 'als Ebook verfügbar.')
    url=u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0[]='+search_authors+'&type0[]=Author&lookfor0[]='+search_title+'&type0[]=Title&lookfor0[]=&type0[]=AllFields&bool0[]=AND&illustration=-1&daterange[]=publishDate&publishDatefrom=&publishDateto='
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        journal_page = response.read()
    journal_page=journal_page.decode('utf-8')
    resultcount=str(ast.literal_eval(str(journal_page))["resultCount"])
    if resultcount>'0' and ebook==False:
        for entry in ast.literal_eval(str(journal_page))["records"]:
            if "[Rez.zu]" not in entry["title"]:
                print(entry["title"])
                sysnumber=str(ast.literal_eval(str(journal_page))["records"][0]["id"])
                if title in ["Reconstructing Damon: Music, Wisdom Teaching, and Politics in Perikles' Athens","The Origins of Ancient Vietnam", "Athenian Prostitution: The Business of Sex",
                             "Archaic and Classical Greek Sicily: A Social and Economic History", "Divine Epiphany in Greek Literature and Culture", "Postcolonial Amazons: Female Masculinity and Courage in Ancient Greek and Sanskrit Literature"
                                                                                                                                                     "Staging Memory, Staging Strife: Empire and Civil War in the Octavia", "The Emperor of Law: The Emergence of Roman Imperial Adjudication"]:
                    ebook=True
                if ebook==True:
                    print('Kein Datensatz erstellt, unter', sysnumber, 'als Ebook verfügbar.')
                else:
                    print('Print:', sysnumber)
    if ebook!=True:
        url=u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0[]='+search_review+'+[Rez.zu]&type0[]=Title&lookfor0[]=&type0[]=AllFields&bool0[]=AND&illustration=-1&daterange[]=publishDate&publishDatefrom='+str(int(year)-3)+'&publishDateto='
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            journal_page = response.read()
        journal_page=journal_page.decode('utf-8')
        resultcount_review=str(ast.literal_eval(str(journal_page))["resultCount"])
        if resultcount_review>'0':
            for entry in ast.literal_eval(str(journal_page))["records"]:
                print(entry["title"])
                print("Review:", entry["id"])
    if resultcount=='0':
        if len(search_authors.rsplit("+", 1))>=2:
            adjusted_search_authors=search_authors.rsplit("+", 1)[1]
        else:
            adjusted_search_authors=search_authors
        search_review=search_title+"+"+adjusted_search_authors
        ebook=False
        url=u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0[]='+adjusted_search_authors+'&type0[]=Author&lookfor0[]='+search_title+'&type0[]=Title&lookfor0[]=Oxford+Scholarship+Online&type0[]=AllFields&bool0[]=AND&illustration=-1&daterange[]=publishDate&publishDatefrom=&publishDateto='
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            journal_page = response.read()
        journal_page=journal_page.decode('utf-8')
        resultcount=str(ast.literal_eval(str(journal_page))["resultCount"])
        if resultcount>'0':
            for entry in ast.literal_eval(str(journal_page))["records"]:
                if "[Rez.zu]" not in entry["title"]:
                    print(entry["title"])
                    ebook=True
                    sysnumber=str(ast.literal_eval(str(journal_page))["records"][0]["id"])
                    print('Kein Datensatz erstellt, unter', sysnumber, 'als Ebook verfügbar.')
        url=u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0[]='+adjusted_search_authors+'&type0[]=Author&lookfor0[]='+search_title+'&type0[]=Title&lookfor0[]=&type0[]=AllFields&bool0[]=AND&illustration=-1&daterange[]=publishDate&publishDatefrom=&publishDateto='
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            journal_page = response.read()
        journal_page=journal_page.decode('utf-8')
        resultcount=str(ast.literal_eval(str(journal_page))["resultCount"])
        if resultcount>'0' and ebook==False:
            for entry in ast.literal_eval(str(journal_page))["records"]:
                if "[Rez.zu]" not in entry["title"]:
                    print(entry["title"])
                    sysnumber=str(ast.literal_eval(str(journal_page))["records"][0]["id"])
                    if title in ["Reconstructing Damon: Music, Wisdom Teaching, and Politics in Perikles' Athens","The Origins of Ancient Vietnam", "Athenian Prostitution: The Business of Sex",
                                 "Archaic and Classical Greek Sicily: A Social and Economic History", "Divine Epiphany in Greek Literature and Culture", "Postcolonial Amazons: Female Masculinity and Courage in Ancient Greek and Sanskrit Literature"
                                                                                                                                                         "Staging Memory, Staging Strife: Empire and Civil War in the Octavia", "The Emperor of Law: The Emergence of Roman Imperial Adjudication"]:
                        ebook=True
                    if ebook==True:
                        print('Kein Datensatz erstellt, unter', sysnumber, 'als Ebook verfügbar.')
                    else:
                        print('Print:', sysnumber)
        if ebook!=True:
            url=u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0[]='+search_review+'+[Rez.zu]&type0[]=Title&lookfor0[]=&type0[]=AllFields&bool0[]=AND&illustration=-1&daterange[]=publishDate&publishDatefrom='+str(int(year)-3)+'&publishDateto='
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                journal_page = response.read()
            journal_page=journal_page.decode('utf-8')
            resultcount_review=str(ast.literal_eval(str(journal_page))["resultCount"])
            if resultcount_review>'0':
                for entry in ast.literal_eval(str(journal_page))["records"]:
                    print(entry["title"])
                    print("Review:", entry["id"])
    if resultcount=='0' and resultcount_review=='0':
        print("\033[45m"+title+"\033[0m")
    print()
    return ebook
#definition für create_review_title

def swagger_find_reviewed_article(recent_record, title, author_names, editor_names, year):
    search_title=""
    word_nr=0
    search_authors=""
    name_nr=0
    for author_name in author_names:
        name_nr+=1
        if name_nr<=1:
            for name in author_name.split(" "):
                name=urllib.parse.quote(name, safe='')
                if ("." not in name):
                    search_authors=search_authors+"+"+name
    search_authors=search_authors.strip("+")
    for editor_name in editor_names:
        name_nr+=1
        if name_nr<=2:
            for name in editor_name.split(" "):
                name=urllib.parse.quote(name, safe='')
                if ("." not in name):
                    search_authors=search_authors+"+"+name
    search_authors=search_authors.strip("+")
    for word in RegexpTokenizer(r'\w+').tokenize(title):
        if (word_nr<7) and (len(word)>3):
            word=urllib.parse.quote(word, safe='')
            search_title=search_title+"+"+word
            word_nr+=1
    search_title=search_title.strip("+")
    ebook=swagger_search_ebook(search_title, search_authors, recent_record, year, title)
    return ebook

def create_245_and_246(recent_record, title, nonfiling_characters, author_nr):
    recent_record.add_field(Field(tag='245', indicators = [str(author_nr), nonfiling_characters], subfields = ['a', title]))

def determine_nonfiling_characters(recent_record, title, year):
    nonfiling_characters=0
    language='eng'
    recent_record.add_field(Field(tag='041', indicators = ['1', ' '], subfields = ['a', language]))
    if language in language_articles.keys():
        first_word=(title.split()[0]).lower()
        if first_word in language_articles[language]:
            nonfiling_characters=str(len(first_word)+1)
    time_str=arrow.now().format('YYMMDD')
    data_008=str(time_str)+'s'+ year + '    ' + 'enk' + ' |   o     |    |' + language  +' d'
    recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
    return nonfiling_characters

def create_new_record(ebook_soup, out, link, url):
        pages=None
        volume=None
        abstract_text=ebook_soup.find('p', attrs={'id':'contentAbstract_full'}).text
        recent_record=Record(force_utf8=True)
        recent_record.add_field(Field(tag='336', indicators = [' ', ' '], subfields = ['a', 'text', 'b', 'txt', '2', 'rdacontent']))
        authors=ebook_soup.find_all('h3', class_='author')
        author_names=[]
        editor_names=[]
        roles=[]
        responsibles=ebook_soup.find('div', id='bookAuthors').find_all('p', class_='author')
        for responsible in responsibles:
            role=responsible.find('em').text
            if role=='author':
                author_names.append((responsible.text).split(", ")[0])
            elif role=='editor':
                editor_names.append((responsible.text).split(", ")[0])
        if len(author_names)>=1:
            editor_names=[]
        authors=[]
        title=ebook_soup.find('meta', attrs={'name':'citation_title'})['content']
        isbn=ebook_soup.find('meta', attrs={'name':'citation_isbn'})['content']
        publisher=ebook_soup.find('meta', attrs={'name':'citation_publisher'})['content']
        year=ebook_soup.find('meta', attrs={'property':'article:published_time'})['content'][0:4]
        doi='https://doi.org/'+ebook_soup.find('meta', attrs={'name':'dc.identifier'})['content']
        author_nr=0
        for author in author_names:
            name=HumanName(author)
            author=(name.last+", "+name.first+" "+name.middle).strip()
            if author_nr==0:
                recent_record.add_field(Field(tag='100', indicators = ['1', ' '], subfields = ['a', author, 'e', 'author']))
                author_nr+=1
            else:
                recent_record.add_field(Field(tag='700', indicators = ['1', ' '], subfields = ['a', author, 'e', 'author']))
                author_nr=author_nr
        for editor in editor_names:
            name=HumanName(editor)
            editor=(name.last+", "+name.first+" "+name.middle).strip()
            recent_record.add_field(Field(tag='700', indicators = ['1', ' '], subfields = ['a', editor, 'e', 'editor']))

        if doi != None:
            recent_record.add_field(Field(tag='024', indicators = ['7', ' '], subfields = ['a', doi, '2', 'doi']))
        recent_record.add_field(Field(tag='040', indicators = [' ', ' '], subfields = ['a', 'FID-ALT-KA-DE-16', 'd', 'DE-2553']))
        recent_record.leader = recent_record.leader[:5] + 'nab a       uu ' + recent_record.leader[20:]
        recent_record.add_field(Field(tag='500', indicators = [' ', ' '], subfields = ['a', 'Fachinformationsdienst Altertumswissenschaften (FID) Propylaeum: Sie können auf dieses Volltext-Angebot zugreifen, \
sofern Sie sich registriert haben und zum berechtigten Nutzerkreis gehören. Weitere Informationen finden Sie hier: https://www.propylaeum.de/service/fid-lizenzen/']))
        recent_record.add_field(Field(tag='500', indicators = [' ', ' '], subfields = ['a', 'Propylaeum – Fachinformationsdienst Altertumswissenschaften ist der, gemeinsam von der Bayerischen Staatsbibliothek München und der Universitätsbibliothek Heidelberg, betriebene Fachinformationsdienst Altertumswissenschaften. Im Kontext der aktuellen Förderung durch die DFG sorgt Propylaeum mit Hilfe sogenannter „FID-Lizenzen“ auch für die überregionale Bereitstellung lizenzpflichtiger digitaler Medien.']))
        recent_record.add_field(Field(tag='520', indicators = ['3', ' '], subfields = ['a', abstract_text]))
        recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'arom']))
        recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', '2019xhnxosoe']))
        recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'online publication']))
        recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'ebookfid0519']))
        recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'fidoso']))
        recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'tu'))
        nonfiling_characters=determine_nonfiling_characters(recent_record, title, year)
        print_title=title
        create_245_and_246(recent_record, print_title, nonfiling_characters, author_nr)
        recent_record.add_field(Field(tag='260', indicators = [' ', ' '],
                                      subfields = ['a', 'Oxford', 'b', publisher, 'c', year]))
        recent_record.add_field(Field(tag='856', indicators = ['4', '0'],
                                          subfields = ['z', 'Available online for registered users of FID', 'u', link, 'x', 'Oxford Scholarship Online']))
        recent_record.add_field(Field(tag='856', indicators = ['4', '1'],
                                          subfields = ['z', 'Table of Contents', 'u', url]))
        #print(recent_record)
        ebook=swagger_find_reviewed_article(recent_record, title, author_names, editor_names, year)
        if ebook!=True:
            out.write(recent_record.as_marc21())

out=None
record_nr=0
url='https://altertum.fid-lizenzen.de/angebote/nlproduct.2015-06-24.3559356258'
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
for link in links:
    if link.find("a")!=None:
        linklist.append(link.find("a")['href'])
linklist=linklist[4:]
out=open('records/oso/oso.mrc', 'wb')
for link in linklist:
    url=link.replace("http://proxy.fid-lizenzen.de/han/oup-ebooks-altertum", "http:/")
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
    values = {'name': 'Helena Nebel',
              'location': 'Berlin',
              'language': 'Python' }
    headers = {'User-Agent': user_agent}
    data = urllib.parse.urlencode(values)
    data = data.encode('ascii')
    req = urllib.request.Request(url, data, headers)
    with urllib.request.urlopen(req) as response:
        ebook_page = response.read()
    ebook_page=ebook_page.decode('utf-8')
    ebook_soup=BeautifulSoup(ebook_page, 'html.parser')
    create_new_record(ebook_soup, out, link, url)
