import urllib.parse, urllib.request
from pymarc import Record, Field
import arrow
import language_codes
from bs4 import BeautifulSoup
import os
from pdf2image import convert_from_path
import tempfile

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
            print(year+issue.replace(".", "_")+str(record_nr), "wurde erstellt.")
        except:
            print(year+issue.replace(".", "_")+str(record_nr), "konnte nicht erstellt werden.")

def urn_is_valid(urn):
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
    values = {'name': 'Helena Nebel',
              'location': 'Berlin',
              'language': 'Python'}
    headers = {'User-Agent': user_agent}
    data = urllib.parse.urlencode(values)
    data = data.encode('ascii')
    try:
        req = urllib.request.Request(urn, data, headers)
        with urllib.request.urlopen(req) as response:
            urn_page = response.read()
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
    language = language_codes.resolve(article_soup.find('meta', attrs={'name': 'DC.Language'})['content'])
    recent_record.add_field(Field(tag='041', indicators=['1', ' '], subfields=['a', language]))
    if language in language_articles.keys():
        first_word = (title.split()[0]).lower()
        if first_word in language_articles[language]:
            nonfiling_characters = str(len(first_word) + 1)
    data_008 = str(time_str) + 's' + year + '    ' + 'gw ' + ' |   o     |    |' + language + ' d'
    recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
    return nonfiling_characters

def create_new_record(article_soup, out, article_url, pdf, pages, issue, record_nr):
    pdf=pdf.replace("view", "download")
    recent_record = Record(force_utf8=True)
    abstract_text = article_soup.find('meta', attrs={'name': 'DC.Description'})['content']
    authors = article_soup.find_all('meta', attrs={'name': 'citation_author'})
    author_names = []
    for author in authors:
        author_names.append(author['content'])
    authors = author_names
    author_nr = 0
    for author in authors:
        author = author.rsplit(" ", 1)[1] + ", " + author.rsplit(" ", 1)[0]
        if author_nr == 0:
            recent_record.add_field(Field(tag='100', indicators=['1', ' '], subfields=['a', author]))
            author_nr += 1
        else:
            recent_record.add_field(Field(tag='700', indicators=['1', ' '], subfields=['a', author]))
            author_nr = author_nr
    title = article_soup.find('meta', attrs={'name': 'citation_title'})['content']
    recent_record.add_field(Field(tag='006', indicators=None, data='m        d        '))
    recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'tc'))
    urn_divs=article_soup.find('div', class_= 'panel-body').find_all('div')
    urns=[urn_div.find('a')['href'] for urn_div in urn_divs if urn_is_valid(urn_div.find('a')['href'])==True]
    for urn in urns:
        recent_record.add_field(Field(tag='024', indicators=['7', ' '], subfields=['a', urn, '2', 'urn', 'q', 'pdf']))
    recent_record.add_field(Field(tag='040', indicators=[' ', ' '], subfields=['a', 'DE-2553']))
    recent_record.add_field(Field(tag='336', indicators=[' ', ' '], subfields=['a', 'text', 'b', 'txt', '2', 'rdacontent']))
    recent_record.add_field(Field(tag='337', indicators=[' ', ' '], subfields=['a', 'computer', 'b', 'c', '2', 'rdamedia']))
    recent_record.add_field(Field(tag='338', indicators=[' ', ' '], subfields=['a', 'online resource', 'b', 'cr', '2', 'rdacarrier']))
    recent_record.leader = recent_record.leader[:5] + 'nmb a       uu ' + recent_record.leader[20:]
    recent_record.add_field(Field(tag='520', indicators=['3', ' '], subfields=['a', abstract_text]))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'arom']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', '2019xhnxefb']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'aeforsch']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'daiauf8']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'online publication']))
    recent_record.add_field(Field(tag='500', indicators=[' ', ' '], subfields=['a', 'First published in '+year]))
    print_title = title
    nonfiling_characters = determine_nonfiling_characters(recent_record, title, year)
    create_245_and_246(recent_record, print_title, nonfiling_characters, author_nr)
    recent_record.add_field(Field(tag='264', indicators=[' ', '1'], subfields=['a', 'Berlin', 'b', 'Deutsches Archäologisches Institut', 'c', year]))
    if year<'2018':
        recent_record.add_field(Field(tag='264', indicators=[' ', '1'], subfields=['c', '©'+year]))
    if pdf != None:
        recent_record.add_field(Field(tag='856', indicators=['4', '1'],
                                      subfields=['z', 'application/pdf', 'u', pdf]))
    recent_record.add_field(Field(tag='856', indicators=['4', '1'],
                                  subfields=['z', 'Table of Contents', 'u', list_element]))
    recent_record.add_field(Field(tag='LKR', indicators=[' ', ' '],
                                          subfields=['a', 'ANA', 'b', '001376930', 'l', 'DAI01',
                                                     'm', title, 'n', 'e-Forschungsberichte des DAI, ' +issue+" ("+year+")", 'x', '2198-7734']))
    if issue == None:
        issue = article_soup.find('a', class_='title').text.split("Nr. ")[1].split(" (")[0]
    recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', issue+', '+pages]))
    #title = title.replace("/", ",")[:200]
    #create_jpgs(pdf, record_nr, title)
    out.write(recent_record.as_marc21())


out = None
issues = []
url = 'https://publications.dainst.org/journals/index.php/efb'
record_nr = 0
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
h4_elements = journal_soup.find_all('h4')
h4_elements=h4_elements[:-1]
list_elements=[]
for element in h4_elements:
    list_elements.append(element.find('a')['href'])
already_harvested=["https://publications.dainst.org/journals/index.php/efb/issue/view/166", "https://publications.dainst.org/journals/index.php/efb/issue/view/162", "https://publications.dainst.org/journals/index.php/efb/issue/view/2"]
for list_element in list_elements:
    #if list_elements.index(list_element)>=1:
        #break
    if list_element in already_harvested:
        continue
    else:
        url = list_element
        req = urllib.request.Request(url, data, headers)
        with urllib.request.urlopen(req) as response:
            issue_page = response.read().decode('utf-8')
        issue_soup = BeautifulSoup(issue_page, 'html.parser')
        year=issue_soup.find('h2').text
        issue=issue_soup.find_all('h3')[0].text.replace("zikel ", "c.")
        issue_file_name = year + "_" + issue
        if issue_file_name not in issues:
            out = open("efb/"+issue_file_name+".mrc", 'wb')
        article_nr = 0
        for article in issue_soup.find_all('table', class_='tocArticle')[1:]:
            article_url = article.find('div', class_='tocTitle').find('a')['href'].strip()
            pdf = article.find('div', class_='tocGalleys').find('a')['href'].strip()
            pages = article.find('div', class_='tocPages').text.strip()
            article_nr += 1
            req = urllib.request.Request(article_url, data, headers)
            with urllib.request.urlopen(req) as response:
                issue_page = response.read().decode('utf-8')
            article_soup = BeautifulSoup(issue_page, 'html.parser')
            #print(article_soup)
            create_new_record(article_soup, out, article_url, pdf, pages, issue, record_nr)
            record_nr += 1

