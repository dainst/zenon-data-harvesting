import urllib.parse, urllib.request
from pymarc import Record, Field
import os
import arrow
import language_codes
from langdetect import detect
print(os.getcwd())
print(os.path.dirname(__file__))

url = 'https://muse.jhu.edu/journal/399'
user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
values = {'name': 'Lisa Meier',
          'location': 'Tulsa',
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
from bs4 import BeautifulSoup
journal_soup=BeautifulSoup(journal_page, 'html.parser')
list_elements=journal_soup.find_all('li', class_='volume')
nown_languages=[]
for list_element in list_elements:
    time=arrow.now().format('YYMMDD')
    out=open('records/late_antiquity'+(str(list_element.span.a).split('"')[1][6:]+'.mrc'), 'wb')
    url = 'https://muse.jhu.edu' + str(list_element.span.a).split('"')[1]
    issue_name=str(list_element.span.a).split('"')[1][7:]
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
    for article in articles:
        recent_record=Record(force_utf8=True)
        article_nr+=1
        if article.ol.a.text not in ["Volume Table of Contents", "Volume Contents"]:
            recent_record.add_field(Field(tag='336', indicators = [' ', ' '], subfields = ['a', 'text', 'b', 'txt', '2', 'rdacontent']))
            authors=article.ol.find('li', class_='author').find_all('a')
            author_nr=0
            for author in authors:
                if author_nr==0:
                    recent_record.add_field(Field(tag='100', indicators = ['1', ' '], subfields = ['a', author]))
                else:
                    recent_record.add_field(Field(tag='700', indicators = ['1', ' '], subfields = ['a', author]))
            if article.ol.find('li', class_='pg')!=None:
                pages=article.ol.find('li', class_='pg').text
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
                recent_record.add_field(Field(tag='024', indicators = ['7', ' '], subfields = ['a', article.ol.find('li', class_='doi').a.text, '2', 'doi']))
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
                    recent_record.add_field(Field(tag='024', indicators = ['7', ' '], subfields = ['a', article_soup.find('li', class_='doi').a.text, '2', 'doi']))
                #12 Artikel ohne DOI bleiben übrig.
            recent_record.leader = recent_record.leader[:5] + 'nmb a       uu ' + recent_record.leader[20:]
            #wie soll ich das belegen?
            recent_record.add_field(Field(tag='040', indicators = [' ', ' '], subfields = ['a', 'eperiodica', 'd', 'DE-2553']))
            recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'online publication']))
            recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'arom']))
            recent_record.add_field(Field(tag='042', indicators=[' ', ' '], subfields=['a', 'dc']))
            recent_record.add_field(Field(tag='006', indicators=None, subfields=None, data=u'm        u        '))
            recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'cuuuuu   uuauu'))
            title=article.ol.a.text
            nonfiling_characters=0
            try:
                language=language_codes.resolve(detect(title))
            except:
                language="   "
            if language!='   ':
                recent_record.add_field(Field(tag='041', indicators = ['1', ' '], subfields = ['a', language]))
            if language in articles.keys():
                first_word=(title.split()[0]).lower()
                if first_word in articles[language]:
                    nonfiling_characters=str(len(first_word)+1)
            if article.ol.a.i!=None and 'review' in article.ol.a.text:
                title=title.replace(article.ol.a.i.text, '\"'+article.ol.a.i.text+'\"')
                if " by " in article.ol.a.text:
                    if " ed. " in article.ol.a.text:
                        title= "[Rez. zu]: "+title[:-9].split(" by ")[1]+"(Hrsg.): "+title[:-9].split(" ed. by ")[0]
                    else:
                        title= "[Rez. zu]: "+title[:-9].split(" by ")[1]+": " +title[:-9].split(" by ")[0]


            '''if parallel_title_nr==0:
                recent_record.add_field(Field(tag='245', indicators = [str(creator_number), nonfiling_characters], subfields = parallel_title))
            else:
                print(titles)
                recent_record.add_field(Field(tag='246', indicators = [str(creator_number), nonfiling_characters], subfields = parallel_title))
            parallel_title_nr+=1
            #prüfen, ob automatisierte Abfrage des OPACs möglich, um rezensierte Bücher zu finden!!!

            data_008=str(time)+'s'+ year + '    ' + 'us' + '                  ' + language  +' d'
            recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
            if len(authors)==0:
                ...

            if content_list[4][1][0] not in [None,'[s.n.]'] and content_list:
                recent_record.add_field(Field(tag='260', indicators = [' ', ' '],
                                              subfields = ['b', content_list[4][1][0], 'c', content_list[6][1][0][:5]]))
            recent_record.add_field(Field(tag='856', indicators = ['4', '1'],
                                          subfields = ['z', 'Table of Contents', 'u', content_list[14][1][0]]))
            recent_record.add_field(Field(tag='856', indicators = ['4', '1'],
                                          subfields = ['z', 'application/pdf', 'u', content_list[14][1][1]]))
            recent_record.add_field(Field(tag='856', indicators = ['4', '1'],
                                          subfields = ['z', 'Table of Contents', 'u', 'https://doi.org/'+content_list[14][1][2][4:]]))
            volume_nr=(content_list[14][1][0][51:].split("::")[0]).split(":")[1]
            year_of_volume=(content_list[14][1][0][51:].split("::")[0]).split(":")[0]
            if volume_nr!='0':
                recent_record.add_field(Field(tag='LKR', indicators = [' ', ' '],
                                              subfields = ['a', 'ANA', 'b', journal_titles[journal_pid]['SYS'], 'l', 'DAI01',
                                                           'm', titles[0][1], 'n', journal_titles[journal_pid]['TIT']+', '+
                                                           volume_nr+' ('+year_of_volume+')']))
            else:
                recent_record.add_field(Field(tag='LKR', indicators = [' ', ' '],
                                              subfields = ['a', 'ANA', 'b', journal_titles[journal_pid]['SYS'], 'l', 'DAI01',
                                                           'm', titles[0][1], 'n', journal_titles[journal_pid]['TIT']+', '+year_of_volume]))
        '''
        #out.write(recent_record.as_marc21())
        #article_number+=1
    #print("Alle Records wurden erfolgreich erstellt.")
            #print(title)'''

print(article_with_i_nr)
#wollen wir Abstracts?
#wollen wir ein Textmining-Programm über den Abstract laufen lassen?




