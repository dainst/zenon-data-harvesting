import urllib.request
import re
from pymarc import MARCReader
import json
import find_existing_doublets
import os
import sys


for page in range(1, 13114):
    print(page)
    url=u'https://zenon.dainst.org/api/v1/search?type=AllFields&sort=relevance&page='+str(page)+'&limit=100&prettyPrint=false&lng=de'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        journal_page = response.read()
    json_response=journal_page.decode('utf-8')
    json_response=json.loads(json_response)
    for result in json_response['records']:
        webFile = urllib.request.urlopen("https://zenon.dainst.org/Record/"+result['id']+"/Export?style=MARC")
        new_reader = MARCReader(webFile)
        all_results = [result['id']]
        try:
            for file in new_reader:
                if 'b' in file['245']:
                    title = file['245']['a'] + ' ' + file['245']['b']
                else:
                    title = file['245']['a']
                authors = [author_field['a'].split(', ')[0] for author_field in file.get_fields('100', '700')]
                if file.get_fields('260', '264'):
                    year = [min([int(year) for year in re.findall(r'\d{4}', field)]) for field in [field['c'] for field in file.get_fields('260', '264') if field['c']] if '©' not in field and re.findall(r'\d{4}', field)]
                default_lang = 'en'
                possible_host_items = [field['b'] for field in file.get_fields('995') if field['a']=='ANA']
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
                                             'additional_fields': {'[placeholder_for_tag_of_field]': {'indicator_1': '',
                                                                                                      'indicator_2': '',
                                                                                                      'subfields':
                                                                                                          [{'[subfield_code]':
                                                                                                                '[subfield_content]'}]}},
                                             # In diesem Feld werden zusätzliche Felder angegeben, die nicht durch die angegebenen Daten
                                             # abgedeckt sind.
                                             'default_language': '',
                                             # Sprache, in der die Publikation mit der höchsten Wahrscheinlichkeit verfasst wurde, falls
                                             # die Spracherkennung scheitert. Das Feld SOLLTE besetzt werden mit dem dreistelligen Code
                                             # für die jeweilige Sprache nach ISO 639-2
                                             'volume': '',
                                             # der default-Wert ist ein leerer String. Volume sollte mit der Angabe der Nummer des
                                             # Bandes der übergeordneten Aufnahme besetzt werden, falls eine übergeordnete Aufnahme
                                             # existiert und die Bandzählung nicht nur in Form der Angabe des Publikationsjahres
                                             # vorgenommen wird.
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
                                                   'year_of _publication': '',
                                                   # Erscheinungsjahr der rezensierten Publikation, muss nicht gesetzt werden, falls
                                                   # verfügbar, verbessert es jedoch die Suche nach der rezensierten Publikation
                                                   }]}
                e_resource = False
                publication_dict['LDR_06_07'] = file.leader[6:8]
                if file['337']:
                    publication_dict['rdamedia'] = str(file['337']['b'])
                if file['338']:
                    publication_dict['rdacarrier'] = str(file['338']['b'])
                if file['006']:
                    publication_dict['field_006'] = file['006'].data
                    if str(file['006'].data)[0] == 'm':
                        publication_dict['rdamedia'] = 'c'
                if file['007']:
                    publication_dict['field_007'] = file['007'].data
                    if str(file['007'])[0:2] == 'cr':
                        publication_dict['rdacarrier'] = 'cr'
                for field in file.get_fields('856'):
                    if 'online' in str(field['z']).lower():
                        publication_dict['pdf_links'].append(str(field['u']))
                if file['300']:
                    if ('online' in str(file['300']['a']).lower()):
                        publication_dict['rdacarrier'] = 'cr'
                        publication_dict['rdamedia'] = 'c'
                if file['533']:
                    if ('online' in str(file['533']['a']).lower()):
                        publication_dict['rdacarrier'] = 'cr'
                        publication_dict['rdamedia'] = 'c'
                if file['590']:
                    if [str(field['a']).lower() for field in file.get_fields('590') if 'online' in str(field['a']) or 'ebook' in str(field['a'])]:
                        publication_dict['rdacarrier'] = 'cr'
                        publication_dict['rdamedia'] = 'c'
                if file['245']['c']:
                    publication_dict['title_dict']['responsibility_statement'] = file['245']['c']
                if year:
                    all_results, additional_physical_form_entrys = find_existing_doublets.find(title, authors, year[0], default_lang, possible_host_items, publication_dict)
                    if result['id'] not in all_results:
                        print('eigener Datensatz nicht gefunden', result['id'], all_results)
                    while result['id'] in all_results:
                        all_results.remove(result['id'])
                    if len(all_results)>=1:
                        print(result['id'], all_results)
                else:
                    print('Jahreszahl fehlt:', result['id'])
        except Exception as e:
            print('Error! Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print(result['id'])

