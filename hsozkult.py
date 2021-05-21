import urllib.parse
import urllib.request
import ast
from bs4 import BeautifulSoup
import re
import os
import sys
from pymarc import MARCReader
import json
import create_new_record

volumes_sysnumbers = {}
url=u'https://zenon.dainst.org/api/v1/search?lookfor=000810356&type=ParentID'
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    journal_page = response.read()
journal_page=journal_page.decode('utf-8')
results=ast.literal_eval(str(journal_page))["records"]
for result in results:
    webFile = urllib.request.urlopen("https://zenon.dainst.org/Record/"+str(result['id'])+"/Export?style=MARC")
    new_reader = MARCReader(webFile)
    for file in new_reader:
        pub_date = ""
        for field in ['260', '264']:
            if file[field] is not None:
                pub_date = re.findall(r'\d{4}', file[field]['c'])[0]
        volumes_sysnumbers[pub_date] = result['id']


#alles im Fachbereich Archäologie: https://www.hsozkult.de/publicationreview/page?sort=newestPublished&fq=category_discip%3A%223/103/127%22
out=None
publication_years=[]
record_nr = 0
empty_page = False
page = 0
while not empty_page:
    page += 1
    try:
        url = 'https://www.hsozkult.de/publicationreview/page?page='+str(page)
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
        values = {'name': 'Helena Nebel',
                  'location': 'Berlin',
                  'language': 'Python' }
        headers = {'User-Agent': user_agent}
        data = urllib.parse.urlencode(values)
        data = data.encode('ascii')
        req = urllib.request.Request(url, data, headers)
        with urllib.request.urlopen(req) as response:
            journal_page = response.read()
        journal_page=journal_page.decode('utf-8')
        journal_soup=BeautifulSoup(journal_page, 'html.parser')
        list_elements=journal_soup.find_all('div', class_="hfn-list-itemtitle")
        list_elements=['https://www.hsozkult.de'+list_element.find('a')['href'] for list_element in list_elements if list_element.find('a')is not None]
        if not list_elements:
            empty_page = True
        for review_url in list_elements:
            try:
                publication_dict = {'title_dict':
                                        {'main_title': '', 'sub_title': '', 'parallel_title': '', 'responsibility_statement': ''},
                                    # der default-Wert für die einzelnen Werte im title-dict ist jeweils ein leerer String,
                                    # andere Werte sind nicht erlaubt.
                                    'authors_list': [], 'editors_list': [],
                                    # der default-Wert für die Listen der Autoren- und Herausgebernamen ist eine leere Liste,
                                    # andere Werte sind nicht erlaubt. Falls die Liste befüllt wird, sind die einzelnen
                                    # Listenelemente die Namen der entsprechenden Personen in der invertierten Form 'NN, VN'
                                    'abstract_link': '',
                                    # der Default-Wert ist ein leerer String, falls vorhanden, wird an dieser Stelle der
                                    # Link zu der Website eingefügt, auf der das Abstract abgerufen werden kann.
                                    'table_of_contents_link': '',
                                    # der Default-Wert ist ein leerer String, falls vorhanden, wird an dieser Stelle der
                                    # Link zu der Website eingefügt, auf der das Inhaltsverzeichnis der übergeordneten
                                    # Ressource bzw. der Ressource selbst abgerufen werden kann
                                    'pdf_links': [],
                                    # der Default-Wert ist ein leerer String, falls vorhanden, wird an dieser Stelle der
                                    # Link eingefügt, unter dem die Ressource als pdf-Dokument abgerufen werden kann
                                    'html_links': [],
                                    # der Default-Wert ist ein leerer String, falls vorhanden, wird an dieser Stelle der
                                    # Link eingefügt, unter dem die Ressource als html-Dokument abgerufen werden kann
                                    'other_links_with_public_note': [{'public_note': '', 'url': ''}],
                                    # der Default-Wert ist eine Liste, die ein Dictionary enthält, dessen Schlüssel auf leere
                                    # Werte verweisen. Falls hier weitere Links eingefügt werden sollen, sollte der
                                    # Displaytext, der im OPAC angezeigt wird, in 'public note' und die url anbgegeben werden.
                                    # Jeder Link zu einer Ressource wird durch ein einzelnes Dictionary repräsentiert.
                                    'doi': '',
                                    # der default-Wert ist ein leerer String, falls vorhanden, wird hier die angegebene doi
                                    # ohne eventuelle Präfixe eingefügt. Die Validität der doi muss nicht überprüft werden, das
                                    # Programm übernimmt diese nur, wenn ein DOI-Resolver das referenzierte Dokument findet.
                                    'urn': '',
                                    # siehe doi, die urn wird NICHT auf Validität überprüft, da kein allgemeingültiges
                                    # Resolving-System existiert.
                                    'isbn': '',
                                    # Angabe der ISBN falls vorhanden im Falle von Monographien
                                    'text_body_for_lang_detection': '',
                                    # Der default-Wert ist ein leerer String, falls vorhanden, können hier der Text eines
                                    # Abstracts, summarys oder der Volltext als Textstring übergeben werden, da die
                                    # Spracherkennung auf der Basis eines längeren Textes deutlich besser funktioniert.
                                    'fields_590': [],
                                    # der Default-Wert ist eine leere Liste, hier werden alle Werte als Listenelemente
                                    # angegeben, die in Feld 590, Unterfeld a stehen sollen.
                                    'original_cataloging_agency': '',
                                    # es wird an dieser Stelle die Herkunft der geharvesteten Daten angegeben. Falls ein Sigel
                                    # vorhanden ist, wird das Sigel der aKörperschaft angegeben. Das Feld MUSS gesetzt werden.
                                    'publication_year': '',
                                    # das Feld MUSS belegt werden mit einem String, der vier Ziffern enthält.
                                    'field_300': '',
                                    # das Feld enthält den Wert, der in Feld 300, Unterfeld a gesetzt werden soll.
                                    'publication_etc_statement':
                                        {'production': {'place': '', 'responsible': '', 'country_code': ''},
                                         'publication': {'place': '', 'responsible': '', 'country_code': ''},
                                         'distribution': {'place': '', 'responsible': '', 'country_code': ''},
                                         'manufacture': {'place': '', 'responsible': '', 'country_code': ''}},
                                    # Das Dictionary enthält die Angaben zur Veröffentlichung etc. gemäß
                                    # https://www.loc.gov/marc/bibliographic/bd264.html Unterfeld a, b und c.
                                    # Default-Wert ist das hier angegebene Dictionary mit den eingetragenen Angaben.
                                    'copyright_year': '',
                                    # Falls das Copyright-Datum vom Erscheinungsjahr abweicht, wird das Copyright-Jahr
                                    # hier aufgenommen.
                                    'rdacontent': '',
                                    # Code gemäß https://www.loc.gov/standards/valuelist/rdacontent.html
                                    'rdamedia': '',
                                    # Code gemäß https://www.loc.gov/standards/valuelist/rdamedia.html
                                    'rdacarrier': '',
                                    # Code gemäß https://www.loc.gov/standards/valuelist/rdacarrier.html
                                    'host_item': {'sysnumber': '', 'name': ''},
                                    # der default-Wert ist das Dictionary in der angegebenen Form. Es werden die Zenon-ID und
                                    # der Name der übergeordneten Aufnahme angegeben. Es kann nur ein Host-Item angegeben
                                    # werden.
                                    'LDR_06_07': '',
                                    # Belegung der Positionen 06 und 07 des Leaders als String
                                    # lt. https://www.loc.gov/marc/bibliographic/bdleader.html
                                    # Das Feld MUSS gesetzt werden.
                                    'field_006': '',
                                    # Belegung des Feldes 006 laut https://www.loc.gov/marc/bibliographic/bd006.html
                                    'field_007': '',
                                    # Belegung des Feldes 007 laut https://www.loc.gov/marc/bibliographic/bd007.html
                                    'field_008_18-34': '',
                                    # Belegung des Feldes 008 Position 18-34 laut
                                    # https://www.loc.gov/marc/bibliographic/bd008.html
                                    'field_008_06': '',
                                    # Belegung des Feldes 008 Position 06 laut
                                    # https://www.loc.gov/marc/bibliographic/bd008.html
                                    'additional_fields': [{'tag': '', 'indicators': ['', ''],
                                                           'subfields':
                                                               []}],
                                    # In diesem Feld werden zusätzliche Felder angegeben, die nicht durch die angegebenen Daten
                                    # abgedeckt sind.
                                    # subfields als liste angeben in der Form [subfield_code, Inhalt, subfield_code, Inhalt]
                                    'default_language': '',
                                    # Sprache, in der die Publikation mit der höchsten Wahrscheinlichkeit verfasst wurde, falls
                                    # die Spracherkennung scheitert. Das Feld SOLLTE besetzt werden mit dem dreistelligen Code
                                    # für die jeweilige Sprache nach ISO 639-2
                                    'do_detect_lang': True,
                                    'language_field': {'a': [], 'h': ''},
                                    # das Feld sollte nur dann belegt werden, wenn es sich um eine mehrsprachige
                                    # Publikation handelt oder um eine Publiaktion, die aus einer anderen Sprache übersetzt wurde.
                                    'volume': '',
                                    # der default-Wert ist ein leerer String. Volume sollte mit der Angabe der Nummer des
                                    # Bandes der übergeordneten Aufnahme besetzt werden, falls eine übergeordnete Aufnahme
                                    # existiert und die Bandzählung nicht nur in Form der Angabe des Publikationsjahres
                                    # vorgenommen wird.
                                    'pages': '',
                                    # wird belegt, falls Teil einer übergeordneten Aufnahme.
                                    # Form: pp. x-y
                                    'response': '',
                                    'retro_digitization_info': {'place_of_publisher': '', 'publisher': '', 'date_published_online': ''},
                                    # hier werden die Informationen zur Retrodigitalisierung angegeben, falls es sich um ein Retrodigitalisat handelt.
                                    'review': False,
                                    # wird auf True gesetzt, falls es sich bei der Publikation um eine Rezension handelt. Wenn
                                    # True gesetzt wird, MUSS Review-List befüllt werden.
                                    'review_list':
                                    # der default-Wert ist das Dictionary in der angegebenen Form, ausgefüllt wird es, falls
                                    # es sich um eine Rezension handelt.
                                        [{'reviewed_title': '',
                                          # Titel des rezensierten Werkes, MUSS gesetzt werden.
                                          'reviewed_authors': [],
                                          'reviewed_editors': [],
                                          # Liste der Autoren/Herausgeber des rezensierten Werkes in Falls die Liste befüllt wird,
                                          # sind die einzelnen Listenelemente die Namen der entsprechenden Personen in der
                                          # invertierten Form 'NN, VN'
                                          'year_of_publication': '',
                                          # Erscheinungsjahr der rezensierten Publikation, muss nicht gesetzt werden, falls
                                          # verfügbar, verbessert es jedoch die Suche nach der rezensierten Publikation
                                          }],
                                    'response_list':
                                    # der default-Wert ist das Dictionary in der angegebenen Form, ausgefüllt wird es, falls
                                    # es sich um eine Rezension handelt.
                                        [{'reviewed_title': '',
                                          # Titel des rezensierten Werkes, MUSS gesetzt werden.
                                          'reviewed_authors': [],
                                          'reviewed_editors': [],
                                          # Liste der Autoren/Herausgeber des rezensierten Werkes in Falls die Liste befüllt wird,
                                          # sind die einzelnen Listenelemente die Namen der entsprechenden Personen in der
                                          # invertierten Form 'NN, VN'
                                          'year_of_publication': '',
                                          # Erscheinungsjahr der rezensierten Publikation, muss nicht gesetzt werden, falls
                                          # verfügbar, verbessert es jedoch die Suche nach der rezensierten Publikation
                                          }]}
                rejected_titles = []
                req = urllib.request.Request(review_url)
                with urllib.request.urlopen(req) as response:
                    review_page = response.read()
                review_soup=BeautifulSoup(review_page, 'html.parser')
                year = re.findall(r'\d{4}', review_soup.find('meta', attrs={'name': 'DC.Issued'})['content'])[0]
                if year not in publication_years:
                    out=open('records/hsozkult/hsozkult_'+year+'_0.mrc', 'wb')
                    publication_years.append(year)
                if record_nr%20 == 0:
                    out=open('records/hsozkult/hsozkult_'+year+'_'+str(int(record_nr/20))+'.mrc', 'wb')
                publication_dict['authors_list'] = [author_tag['content'] for author_tag in review_soup.find_all('meta', attrs={'name':'DC.Creator'})]
                publication_dict['html_links'].append(review_soup.find_all('meta', attrs={'name':'DC.Identifier'})[0]['content'])
                publication_year = ""
                publication_dict['text_body_for_lang_detection'] = review_soup.find_all('div', class_="hfn-item-fulltext")[0].text
                mainEntity_div_tag = review_soup.find_all('div')[review_soup.find_all('div').index(review_soup.find_all('div', class_="hfn-item-fulltext")[0])+1]
                for pub in mainEntity_div_tag.find_all('span', class_="mainEntity", itemproperty="mainEntity"):
                    title_reviewed = pub.find('span', itemprop="name").text.strip(' .').strip()
                    publication_year = ''
                    if pub.find_all('span', itemproperty="datePublished"):
                        publication_year = pub.find_all('span', itemproperty="datePublished")[0].text
                    authors_reviewed, editors_reviewed = [], []
                    if pub.find('span', itemprop="author"):
                        authors_reviewed = [author for author in pub.find('span', itemprop="author").text.split('; ')]
                    if pub.find('span', itemprop="editor"):
                        editors_reviewed = [editor for editor in pub.find('span', itemprop="editor").text.split('; ')]
                    publication_dict['review_list'].append({'reviewed_title': title_reviewed,
                                                            'reviewed_authors': authors_reviewed,
                                                            'reviewed_editors': editors_reviewed,
                                                            'year_of_publication': publication_year,
                                                            })
                publication_dict['LDR_06_07'] = 'ab'
                publication_dict['field_006'] = 'm     o  d |      '
                publication_dict['field_007'] = 'cr  uuu      uuuuu'
                publication_dict['field_008_06'] = 's'
                publication_dict['field_008_18-34'] = 'k| p oo|||||   b|'
                publication_dict['table_of_contents_link'] = url
                publication_dict['original_cataloging_agency'] = 'H-Soz-Kult'
                publication_dict['publication_etc_statement']['publication'] = {'place': 'Berlin',
                                                                                'responsible': 'Humboldt-Universität zu Berlin',
                                                                                'country_code': 'gw '}
                publication_dict['publication_year'] = year
                publication_dict['field_300'] = '1 online resource'
                publication_dict['rdacontent'] = 'txt'
                publication_dict['rdamedia'] = 'c'
                publication_dict['rdacarrier'] = 'cr'
                publication_dict['fields_590'] = ['arom', 'Online publication', '2019xhnxhsoz']
                publication_dict['default_language'] = 'de'
                publication_dict['review'] = True
                publication_dict['host_item']['name'] = 'Historische Literatur: Rezensionszeitschrift von H-Soz-u-Kult'
                if year not in volumes_sysnumbers:
                    correct_sysnumber = False
                    id = ''
                    while correct_sysnumber is False:
                        try:
                            id = re.findall(r'^\w{9}$', input('Bitte geben Sie die Systemnummer der übergeordneten Aufnahme an:'))[0]
                            url = 'https://zenon.dainst.org/api/v1/search?lookfor=id%3A' + id + '&type=AllFields&sort=relevance&page=1&limit=20&prettyPrint=false&lng=de'
                            req = urllib.request.Request(url)
                            with urllib.request.urlopen(req) as response:
                                response = response.read()
                            response = response.decode('utf-8')
                            json_response = json.loads(response)
                            if json_response["resultCount"] == 1:
                                correct_sysnumber = True
                        except:
                            #print('Diese Systemnummer ist nicht korrekt.')
                    publication_dict['host_item']['sysnumber'] = id
                create_new_record.create_new_record(out, publication_dict)
                record_nr += 1
            except Exception as e:
                #print('Error! Code: {c}, Message, {m}'.format(c = type(e).__name__, m = str(e)))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                #print(exc_type, fname, exc_tb.tb_lineno)


    except Exception as e:
        #print('Error! Code: {c}, Message, {m}'.format(c = type(e).__name__, m = str(e)))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #print(exc_type, fname, exc_tb.tb_lineno)
        record_nr += 1