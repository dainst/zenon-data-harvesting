import urllib.parse, urllib.request
from pymarc import Record, Field
import arrow
import language_codes
from langdetect import detect
from nltk.tokenize import RegexpTokenizer
import ast
from bs4 import BeautifulSoup

language_articles={'eng': ['the','a', 'an'], 'fre':['la','le','les','un', 'une', 'l\'', 'il'], 'spa':['el','lo','la','las','los',
        'uno' 'un', 'unos', 'unas', 'una'], 'ger':['das', 'der', 'ein', 'eine', 'die'], 'ita':['gli', 'i','le', 'la', 'l\'',
        'lo', 'il', 'gl\'', 'l']}

def swagger_find_article(search_title, search_authors, year):
    url=u'https://zenon.dainst.org/api/v1/search?lookfor=title%3A'+search_title+'%20AND%20author%3A'+search_authors+'%20AND%20publishDate%3A'+year+'&type=AllFields&sort=relevance&page=1&limit=20&prettyPrint=false&lng=de'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        journal_page = response.read()
    journal_page=journal_page.decode('utf-8')
    resultcount=str(ast.literal_eval(str(journal_page))["resultCount"])
    return resultcount

out=None
volumes_sysnumbers={'2018': '001559108', '2017': '001521166', '2016': '001470725', '2015':'001433155', '2014': '001479933', '2013': '001376375', '2012': '001325845', '2011': '001316753', '2010': '000846623', '2009':'000810765', '2008':'000804909'}
url = 'https://muse.jhu.edu/journal/399'
user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
values = {'name': 'Helena Nebel',
          'location': 'Berlin',
          'language': 'Python' }
headers = {'User-Agent': user_agent}
article_nr=0
article_with_i_nr=0
data = urllib.parse.urlencode(values)
data = data.encode('ascii')
req = urllib.request.Request(url, data, headers)
with urllib.request.urlopen(req) as response:
    journal_page = response.read()
journal_page=journal_page.decode('utf-8')
journal_soup=BeautifulSoup(journal_page, 'html.parser')
list_elements=journal_soup.find_all('li', class_='volume')
issues=[]
issue_nr='0'
for list_element in list_elements:
    time_str=arrow.now().format('YYMMDD')
    url = 'https://muse.jhu.edu' + str(list_element.span.a).split('"')[1]
    if list_element.span.a.text.replace(' ', '_').split(',')[0] not in issues:
        out=open('records/late_antiquity/'+list_element.span.a.text.replace(' ', '_').split(',')[0]
             +'.mrc', 'wb')
        issue_nr='1'
    else:
        out=out
        issue_nr='2'
    issues.append(list_element.span.a.text.replace(' ', '_').split(',')[0])
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
    values = {'name': 'Helena Nebel',
              'location': 'Berlin',
              'language': 'Python' }
    headers = {'User-Agent': user_agent}
    data = urllib.parse.urlencode(values)
    data = data.encode('ascii')
    req = urllib.request.Request(url, data, headers)
    with urllib.request.urlopen(req) as response:
        issue_page = response.read().decode('utf-8')
    issue_soup=BeautifulSoup(issue_page, 'html.parser')
    volume=issue_soup.find_all('a', href="/journal/399")[1].text[6:].split(",", 1)[0]
    year=issue_soup.find_all('a', href="/journal/399")[1].text[6:].split(",", 1)[1][-4:]
    articles=issue_soup.find_all('div', class_='card_text')[1:-1]
    found_articles=0
    for article in articles:
        doi=None
        article_nr+=1
        if article.ol.a.text not in ["Volume Table of Contents", "Volume Contents", "From the Editor", "Bibliography", "From the Guest Editors"]:
            recent_record=Record(force_utf8=True)
            title=article.ol.a.text
            recent_record.add_field(Field(tag='336', indicators = [' ', ' '], subfields = ['a', 'text', 'b', 'txt', '2', 'rdacontent']))
            authors=article.ol.find('li', class_='author').find_all('a')
            search_authors=""
            for author in authors:
                for name in author.text.split(" "):
                    name=urllib.parse.quote(name, safe='')
                    if "." not in name:
                        search_authors=search_authors+"+"+name
            search_authors=search_authors.strip("+")
            search_title=""
            word_nr=0
            adjusted_title=title.split(" by ")[0]
            adjusted_title=adjusted_title.replace("ed.", "").replace("(review)", "")
            for word in RegexpTokenizer(r'\w+').tokenize(adjusted_title):
                if (word not in ["ed", "by", "review"]) and (word_nr<8) and (len(word)>3):
                    word=urllib.parse.quote(word, safe='')
                    search_title=search_title+"+"+word
                    word_nr+=1
            search_title=search_title.strip("+")
            result=swagger_find_article(search_title, search_authors, year)
            if result=='0':
                author=article.ol.find('li', class_='author').find('a')
                search_author=""
                if author!=None:
                    for name in author.text.split(" "):
                        name=urllib.parse.quote(name, safe='')
                        if "." not in name:
                            search_author=search_author+"+"+name
                search_authors=search_author.strip("+")
            if result=='0':
                search_title=""
                word_nr=0
                adjusted_title=title.split(".")[0].split(":")[0]
                ##print(adjusted_title)
                adjusted_title=adjusted_title.split(" by ")[0]
                adjusted_title=adjusted_title.replace("ed.", "").replace("(review)", "")
                for word in RegexpTokenizer(r'\w+').tokenize(adjusted_title):
                    word=urllib.parse.quote(word, safe='')
                    if (word not in ["ed", "by", "review"]) and (word_nr<8) and (len(word)>3):
                        search_title=search_title+"+"+word
                        word_nr+=1
                search_title=search_title.strip("+")
                result=swagger_find_article(search_title, search_authors, year)
            if result=='0':
                authors=article.ol.find('li', class_='author').find_all('a')
                search_authors=""
                for author in authors:
                    search_authors += urllib.parse.quote(author.text.split(" ")[-1], safe='') + "+"
                search_authors=search_authors.strip("+")
                result=swagger_find_article(search_title, search_authors, year)
            if result=='1':
                found_articles+=1
                continue
            author_nr=0
            for author in authors:
                author=author.text.rsplit(" ",1)[1]+", "+author.text.rsplit(" ",1)[0]
                if author_nr==0:
                    recent_record.add_field(Field(tag='100', indicators = ['1', ' '], subfields = ['a', author]))
                    author_nr+=1
                else:
                    recent_record.add_field(Field(tag='700', indicators = ['1', ' '], subfields = ['a', author]))
                    author_nr=author_nr
            if article.ol.find('li', class_='pg')!=None:
                pages=article.ol.find('li', class_='pg').text.replace("pp. ", "").replace("p. ", "")
            else:
                url = 'https://muse.jhu.edu' + str(article.ol.find('li', class_='title').span.a).split('"', 2)[1]
                user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
                values = {'name': 'Helena Nebel',
                      'location': 'Berlin',
                      'language': 'Python' }
                headers = {'User-Agent': user_agent}
                data = urllib.parse.urlencode(values)
                data = data.encode('ascii')
                req = urllib.request.Request(url, data, headers)
                with urllib.request.urlopen(req) as response:
                    article_page = response.read().decode('utf-8')
                article_soup=BeautifulSoup(issue_page, 'html.parser')
                pages=article_soup.find('li', class_='pg').text
            if article.ol.find('li', class_='doi')!= None:
                doi=article.ol.find('li', class_='doi').a.text
                recent_record.add_field(Field(tag='024', indicators = ['7', ' '], subfields = ['a', doi, '2', 'doi']))
            else:
                url = 'https://muse.jhu.edu' + str(article.ol.find('li', class_='title').span.a).split('"', 2)[1]
                user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
                values = {'name': 'Helena Nebel',
                          'location': 'Berlin',
                          'language': 'Python' }
                headers = {'User-Agent': user_agent}
                data = urllib.parse.urlencode(values)
                data = data.encode('ascii')
                req = urllib.request.Request(url, data, headers)
                with urllib.request.urlopen(req) as response:
                    article_page = response.read().decode('utf-8')
                article_soup=BeautifulSoup(issue_page, 'html.parser')
                if article_soup.find('li', class_='doi')!=None:
                    doi=article_soup.find('li', class_='doi').a.text
                    recent_record.add_field(Field(tag='024', indicators = ['7', ' '], subfields = ['a', doi, '2', 'doi']))
                #12 Artikel ohne DOI bleiben übrig.
            recent_record.leader = recent_record.leader[:5] + 'nab a       uu ' + recent_record.leader[20:]
            #wie soll ich das belegen?
            recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'arom']))
            #recent_record.add_field(Field(tag='006', indicators=None, subfields=None, data=u'm        u        '))
            recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'tu'))
            nonfiling_characters=0
            try:
                language=language_codes.resolve(detect(title))
            except:
                language="   "
            if language!='   ':
                recent_record.add_field(Field(tag='041', indicators = ['1', ' '], subfields = ['a', language]))
            if language in language_articles.keys():
                first_word=(title.split()[0]).lower()
                if first_word in language_articles[language]:
                    nonfiling_characters=str(len(first_word)+1)
            if '(review)' in article.ol.a.text:
                nonfiling_characters='1'
                title=title.replace(" (review)", "")
                if "by " in article.ol.a.text:
                    if " ed. " in article.ol.a.text:
                        title= "[Rez. zu]: "+title.split(" ed. by ")[1]+"(Hrsg.): "+title.split(" ed. by ")[0]
                    else :
                        title= "[Rez. zu]: "+title.split(" by ")[1]+": " +title.split(" by ")[0]
                else:
                    title="[Rez. zu]: "+title
            recent_record.add_field(Field(tag='245', indicators = [str(author_nr), nonfiling_characters], subfields = ['a', title]))
            #prüfen, ob automatisierte Abfrage des OPACs möglich, um rezensierte Bücher zu finden!!!

            data_008=str(time_str)+'s'+ year + '    ' + 'mdu' + ' |         |    |' + language  +' d'
            recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
            recent_record.add_field(Field(tag='260', indicators = [' ', ' '],
                                          subfields = ['a', 'Baltimore, MD', 'b', 'Johns Hopkins University Press', 'c', year]))
            if doi!=None:
                recent_record.add_field(Field(tag='856', indicators = ['4', '1'],
                                          subfields = ['z', 'Abstract', 'u', 'https://doi.org/'+doi]))
            recent_record.add_field(Field(tag='LKR', indicators = [' ', ' '],
                                          subfields = ['a', 'ANA', 'b', volumes_sysnumbers[year], 'l', 'DAI01',
                                                       'm', title, 'n', 'Journal of Late Antiquity'+', '+
                                                       volume+' ('+year+')']))
            recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', 'Fasc. '+issue_nr+', '+pages]))
            out.write(recent_record.as_marc21())