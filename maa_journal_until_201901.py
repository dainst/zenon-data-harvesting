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
import find_existing_doublets
import sys

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

list_of_articles_without_pages=['"TOROUD", THE LATE MOTION FOR As-Sb BEARING Cu PRODUCTION FROM 2nd MILLENNIUM B.C. IN IRAN: AN ARCHAEOMETALLURGICAL APPROACH',
                                'MULTIELEMENTAL ICP-MS ANALYSIS OF CLASSICAL PERIOD ARCHAEOLOGICAL CREMATED BONE AND SEDIMENT SAMPLES FROM DEMOSION SEMA POLYANDRIA OF SALAMINOS 35 SITE IN KERAMEIKOS, ATHENS, GREECE',
                                'RESTRUCTURING THE SETTLEMENT PATTERN OF A PERAEAN DEME THROUGH PHOTOGRAMMETRY AND GIS: THE CASE OF PHOINIX (BOZBURUN PENINSULA, TURKEY)',
                                'WOODS OF BYZANTINE TRADE SHIPS OF YENIKAPI (ISTANBUL) AND CHANGES IN WOOD USE FROM 6th TO 11th CENTURY',
                                'SEX DETERMINATION USING THE TIBIA IN AN ANCIENT ANATOLIAN POPULATION',
                                'OLIVE OIL PRODUCTION IN A SEMI-ARID AREA: EVIDENCE FROM ROMAN TELL ES-SUKHNAH, JORDAN',
                                'ANALYTICAL STUDY OF PAINT LAYER IN MURAL PAINTING OF KRABIA SCHOOL (19th century), CAIRO, EGYPT',
                                'ANALYSIS AND CONSERVATION OF AN IRON AGE DAGGER FROM TALL ABU AL-KHARAZ, JORDAN VALLEY: A CASE STUDY',
                                'AN ANCIENT GREEK VETERAN-WARRIOR WITH STAFNE\'S CAVITY', 'MATER ARISING']

language_articles = {'eng': ['the', 'a', 'an'], 'fre': ['la', 'le', 'les', 'un', 'une', 'l\'', 'il'],
                     'spa': ['el', 'lo', 'la', 'las', 'los',
                             'uno' 'un', 'unos', 'unas', 'una'], 'ger': ['das', 'der', 'ein', 'eine', 'die'],
                     'ita': ['gli', 'i', 'le', 'la', 'l\'',
                             'lo', 'il', 'gl\'', 'l']}


def create_jpgs(pdf, record_nr, title):
    webFile = urllib.request.urlopen(pdf)
    pdfFile = open("efb_files/"+year+"_"+title+'.pdf', 'wb')
    pdfFile.write(webFile.read())
    webFile.close()
    pdfFile.close()
    PDF_file = "efb_files/"+year+"_"+title+'.pdf'
    with tempfile.TemporaryDirectory() as path:
        try:
            pages = convert_from_path(PDF_file, 150, output_folder=path)
            newpath = 'pages_jpg_efb/'+year+title
            os.makedirs(newpath)
            page_nr=0
            for page in pages:
                page_nr+=1
                if page_nr!=1:
                    page.save(newpath+"/"+str(page_nr)+'.jpg', 'JPEG')
            #print(year+issue.replace(".", "_")+str(record_nr), "wurde erstellt.")
        except:
            #print(year+issue.replace(".", "_")+str(record_nr), "konnte nicht erstellt werden.")

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
    data_008 = str(time_str) + 's' + year + '    ' + 'gr ' + '     o  d |      ' + language + ' d'
    recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
    return nonfiling_characters

def create_new_record(adjusted_parts_of_title, out, toc, pdf, pages, issue_nr, year, titles_processed):
    try:
        doi=None
        recent_record = Record(force_utf8=True)
        if "DOI:" in adjusted_parts_of_title[-1]:
            possible_doi = "https://www.doi.org/"+(adjusted_parts_of_title[-1].replace("DOI:", "").strip())
            if doi_is_valid(possible_doi)==True:
                doi=possible_doi
                recent_record.add_field(Field(tag='024', indicators=['7', ' '], subfields=['a', doi, '2', 'doi', 'q', 'pdf']))
            del adjusted_parts_of_title[-1]
        authors=[]
        adjusted_parts_of_title[0] =adjusted_parts_of_title[0].replace("  D. S. Reese", "").replace("  K. Samanian", "")
        if len(adjusted_parts_of_title)==3:
            adjusted_parts_of_title = adjusted_parts_of_title[:-1]
        for entry in adjusted_parts_of_title:
            if len(re.findall(r'[a-z]', entry))>=3 and len(re.findall(r'[A-Z]{4}', entry))==0 and adjusted_parts_of_title.index(entry)==1:
                authors = entry.split(", ")
        authors = [author.strip('\t').strip().strip('\t').strip() for author in authors]
        authors = [re.sub(r'[0-9]', '', aut) for author in authors for aut in author.split(' and ')]
        # mehrdimensionale List-Comprehension
        author_nr = 0
        authors = [HumanName(author).last + ", " + HumanName(author).first for author in authors]
        authors_for_search = [HumanName(author).last for author in authors]
        author_nr = 0
        for author in authors:
            if author_nr == 0:
                recent_record.add_field(Field(tag='100', indicators=['1', ' '], subfields=['a', author]))
                author_nr += 1
            else:
                recent_record.add_field(Field(tag='700', indicators=['1', ' '], subfields=['a', author]))
                author_nr = author_nr
        title=adjusted_parts_of_title[0]

        lang=detect(title)
        title_word_list = RegexpTokenizer(r'\w+').tokenize(title)
        title_word_list.sort(key=len, reverse=True)
        for word in title_word_list:
            for item in re.findall(r'(?:^|\W)'+ word + r'(?:\W|$)', title):
                if item[0] == "'" and len(item) == 3:
                    title=title.replace(item, item.replace(word, word.lower()))
                else:
                    title=title.replace(item, item.replace(word, word.capitalize()))
        '''
        if title in [#'Comparative Re-Surveys By Statistics And Gis In Isernia And Venosa (Molise And Basilicata, Italy)', #Index-Problem mit Einschub lösen?
                     'On The Value And Meaning Of Proclus’ Perfect Year',
                     'Metal Jewelry And Socioeconomic Status In Rural Jordan In Late Antiquity',
                     'Identification Of Buried Archaeological Relics Using Derivatives Of Magnetic Anomalies In Olympos Mountain, West Anatolia: A Case Study',
                     'Auditory Exostoses, Infracranial Skeleto-Muscular Changes And Maritime Activities In Classical Period Thasos Island',
                     'Comparison Between The Properties Of "Acceelerated-Aged" Bones And Archaeologcial Bones',
                     'Breaking News: Decoding The Earliest "Computer": The Antikythera Astrolabe. Science And Technology In Ancient Greece',
                     'Dating Of Megalithic Masontry By Luminescence Techniques',
                     'Editorial Addendum: Revival Of Obsidian Studies']:
        '''
        if title not in titles_processed:
            recent_record.add_field(Field(tag='006', indicators=None, data='m     o  d |      '))
            recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'cr uuu   uuuuu'))
            recent_record.add_field(Field(tag='040', indicators=[' ', ' '], subfields=['a', 'MAA', 'd', 'DE-2553']))
            recent_record.add_field(Field(tag='336', indicators=[' ', ' '], subfields=['a', 'text', 'b', 'txt', '2', 'rdacontent']))
            recent_record.add_field(Field(tag='337', indicators=[' ', ' '], subfields=['a', 'computer', 'b', 'c', '2', 'rdamedia']))
            recent_record.add_field(Field(tag='338', indicators=[' ', ' '], subfields=['a', 'online resource', 'b', 'cr', '2', 'rdacarrier']))
            recent_record.leader = recent_record.leader[:5] + 'nab a       uu ' + recent_record.leader[20:]
            recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'arom']))
            recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', '2020xhnxmaa']))
            recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'online publication']))
            nonfiling_characters = determine_nonfiling_characters(recent_record, title, year)
            create_245_and_246(recent_record, title, nonfiling_characters, author_nr)
            titles_processed.append(title)
            recent_record.add_field(Field(tag='264', indicators=[' ', '1'], subfields=['a', 'Rhodes', 'b', 'University of the Aegean', 'c', year]))
            if pdf != None:
                recent_record.add_field(Field(tag='856', indicators=['4', '0'],
                                              subfields=['z', 'application/pdf', 'u', pdf]))
            recent_record.add_field(Field(tag='856', indicators=['4', '2'],
                                          subfields=['z', 'Table of Contents', 'u', toc]))
            recent_record.add_field(Field(tag='LKR', indicators=[' ', ' '],
                                          subfields=['a', 'ANA', 'b', '001560550', 'l', 'DAI01',
                                                     'm', title, 'n', 'Mediterranean Archaeology & Archaeometry, ' +volume+" ("+year+")", 'x', '2241-8121']))
            if pages!=[]:
                recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', 'Fasc.'+issue_nr+', p.'+pages]))
            else:
                recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', 'Fasc.'+issue_nr]))
            resultcount=find_existing_doublets.find(title, authors_for_search, year, 'en', ['000724049'])
            if resultcount>0:
                #print('found:', year, issue_nr, title, authors, 'results:', resultcount)
            else:
                #print('not found:', year, issue_nr, title, authors)
            out.write(recent_record.as_marc21())
        return titles_processed
    except Exception as e:
        #print('Error! Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e)))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #print(exc_type, fname, exc_tb.tb_lineno)

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
    toc = url
    year=re.findall('\d{4}', issue.find('a')['href'])[0]
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
        out = open("maa/"+issue_file_name+".mrc", 'wb')
    article_nr = 0
    article_info_and_pdf=issue_soup.find_all('p')
    article_info_and_pdf.reverse()
    lines_printed=0
    for item in article_info_and_pdf:
        pdf=None
        title=None
        pages=[]
        adjusted_parts_of_title=[]
        if item.find('a')!= None:
            if article_info_and_pdf.index(item)+1<len(article_info_and_pdf):
                if ".pdf" in item.find('a')['href'] and "pp." in article_info_and_pdf[article_info_and_pdf.index(item)+1].text:
                    pdf=item.find('a')['href'].replace("%28", "(").replace("%29", ")").replace("%20", " ")
                    title=article_info_and_pdf[article_info_and_pdf.index(item)+1].text.split("Download PDF")[0]
                    if ("Cover" not in pdf) and ("BOOK REVIEW" not in title):
                        lines_printed+=1
                        parts_of_title=title.split("\n")
                        for part_of_title in parts_of_title:
                            part_of_title=part_of_title.strip('\t').strip().strip('\t').strip()
                            if len(part_of_title)!=0:
                                adjusted_parts_of_title.append(part_of_title)
                        if len(adjusted_parts_of_title)==1:
                            adjusted_parts_of_title=adjusted_parts_of_title[0].rsplit(") ", 1)
                            parts_of_title[0]=parts_of_title[0]+")"
                        if len(adjusted_parts_of_title)==4:
                            seperator=" "
                            adjusted_parts_of_title=[seperator.join(adjusted_parts_of_title[:-1]), adjusted_parts_of_title[-1]]
                        issue_data[year+"_"+volume][pdf]={'title':title, 'year':year, 'volume':volume, 'issue_nr':issue_nr}
                elif ".pdf" in item.find('a')['href'] and "pp." not in article_info_and_pdf[article_info_and_pdf.index(item)+1].text and year=='2014':
                    if "Download PDF" not in article_info_and_pdf[article_info_and_pdf.index(item)+1].text:
                        pdf=item.find('a')['href'].replace("%28", "(").replace("%29", ")").replace("%20", " ")
                        title=article_info_and_pdf[article_info_and_pdf.index(item)+1].text
                        if ("Cover" not in pdf) and ("BOOK REVIEW" not in title):
                            lines_printed+=1
                            parts_of_title=title.split("\n")
                            if len(parts_of_title)==1:
                                parts_of_title=parts_of_title[0].rsplit(") ", 1)
                                parts_of_title[0]=parts_of_title[0]+")"
                            for part_of_title in parts_of_title:
                                part_of_title=part_of_title.strip('\t').strip().strip('\t').strip()
                                if len(part_of_title)!=0:
                                    adjusted_parts_of_title.append(part_of_title)
                            if len(adjusted_parts_of_title)==1:
                                adjusted_parts_of_title=adjusted_parts_of_title[0].rsplit(") ", 1)
                                parts_of_title[0]=parts_of_title[0]+")"
                            issue_data[year+"_"+volume][pdf]={'title':title, 'year':year, 'volume':volume, 'issue_nr':issue_nr}
                if len(adjusted_parts_of_title)!=0:
                    article_nr+=1
                    if adjusted_parts_of_title[0] in ["FAUNAL REMAINS FROM EARLY HELLADIC II", "SUKIAS HOUSE AND ITS WALL PAINTINGS: REFLECTION OF ENGLISH-ARMENIAN LINKS IN THE SAFAVID PERIOD (1501-1736 AD) IN ISFAHAN,"]:
                        seperator=" "
                        adjusted_parts_of_title=[seperator.join((adjusted_parts_of_title))]
                    if adjusted_parts_of_title[0]=="MATER ARISING":
                        del adjusted_parts_of_title[1]
                    pages=re.findall(r'\(pp\..*?\)', adjusted_parts_of_title[0])
                    if (pages==[]) and ("(pp." in adjusted_parts_of_title[0]):
                        adjusted_parts_of_title[0]=adjusted_parts_of_title[0]+")"
                        pages=re.findall(r'\(pp\..*?\)', adjusted_parts_of_title[0])
                    if pages!=[]:
                        adjusted_parts_of_title[0]=adjusted_parts_of_title[0].replace(pages[0], "").strip()
                        pages=pages[0].replace('(', '').replace(')', '').replace('pp.', '').strip()
                    create_new_record(adjusted_parts_of_title, out, toc, pdf, pages, issue_nr, year, titles_processed)
    #print(year, article_nr)