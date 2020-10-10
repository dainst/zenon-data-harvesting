import urllib.parse
import urllib.request
from pymarc import Record
from pymarc import Field
from pymarc import MARCReader
import arrow
import language_codes
from langdetect import detect
import find_reviewed_title
import find_existing_doublets
import re
import write_error_to_logfile


rda_codes = {'rdacarrier': {'sg': 'audio cartridge', 'sb': 'audio belt', 'se': 'audio cylinder', 'sd': 'audio disc',
                            'si': 'sound track reel', 'sq': 'audio roll', 'sw': 'audio wire reel',
                            'ss': 'audiocassette', 'st': 'audiotape reel', 'sz': 'other', 'ck': 'computer card',
                            'cb': 'computer chip cartridge', 'cd': 'computer disc', 'ce': 'computer disc cartridge',
                            'ca': 'computer tape cartridge ', 'cf': 'computer tape cassette',
                            'ch': 'computer tape reel', 'cr': 'online resource', 'cz': 'other', 'ha': 'aperture card',
                            'he': 'microfiche', 'hf': 'microfiche cassette', 'hb': 'microfilm cartridge',
                            'hc': 'microfilm cassette', 'hd': 'microfilm reel', 'hj': 'microfilm roll',
                            'hh': 'microfilm slip', 'hg': 'microopaque', 'hz': 'other', 'pp': 'microscope slide',
                            'pz': 'other', 'mc': 'film cartridge', 'mf': 'film cassette', 'mr': 'film reel',
                            'mo': 'film roll', 'gd': 'filmslip', 'gf': 'filmstrip', 'gc': 'filmstrip cartridge',
                            'gt': 'overhead transparency', 'gs': 'slide', 'mz': 'other', 'eh': 'stereograph card',
                            'es': 'stereograph disc', 'ez': 'other', 'no': 'card', 'nb': 'sheet', 'nc': 'volume'},
             'rdacontent': {'crd': 'cartographic dataset', 'cri': 'cartographic image',
                            'crm': 'cartographic moving image', 'crt': 'cartographic tactile image',
                            'crn': 'cartographic tactile three-dimensional form',
                            'crf': 'cartographic three-dimensional form', 'cod': 'computer dataset',
                            'cop': 'computer program', 'ntv': 'notated movement', 'ntm': 'notated music',
                            'prm': 'performed music', 'snd': 'sounds', 'spw': 'spoken word', 'sti': 'still image',
                            'tci': 'tactile image', 'tcm': 'tactile notated music', 'tcn': 'tactile notated movement',
                            'tct': 'tactile text', 'tcf': 'tactile three-dimensional form', 'txt': 'text',
                            'tdf': 'three-dimensional form', 'tdm': 'three-dimensional moving image',
                            'tdi': 'two-dimensional moving image', 'xxx': 'other', 'zzz': 'unspecified'},
             'rdamedia': {'s': 'audio', 'c': 'computer', 'h': 'microform', 'p': 'microscopic', 'g': 'projected',
                          'e': 'stereographic', 'n': 'unmediated', 'v': 'video'}}

language_articles = {'eng': ['the', 'a', 'an'], 'fre': ['la', 'le', 'les', 'un', 'une', 'l\'', 'il'],
                     'spa': ['el', 'lo', 'la', 'las', 'los',
                             'uno' 'un', 'unos', 'unas', 'una'], 'ger': ['das', 'der', 'ein', 'eine', 'die'],
                     'ita': ['gli', 'i', 'le', 'la', 'l\'',
                             'lo', 'il', 'gl\'', 'l']}

publication_dict_template = {'title_dict':
                             {'main_title': '', 'sub_title': '', 'parallel_titles': [], 'responsibility_statement': ''},
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
                             # das Feld enthält den Wert, der in Feld 300, Unterfeld a gesetzt werden soll. Dieses Feld wird nur dann gesetzt, wenn es sich um eine Monographie handelt!
                             'force_300': False,
                             'force_epub': False,
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
                             'host_item': {'sysnumber': '', 'name': '', 'issn': ''},
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
                             'language_field': {'language_of_resource': [], 'language_of_original_item': ''},
                             # das Feld sollte nur dann belegt werden, wenn es sich um eine mehrsprachige
                             # Publikation handelt oder um eine Publiaktion, die aus einer anderen Sprache übersetzt wurde.
                             # beide Felder werden mit dem ISO 639-2-Code belegt.
                             'volume': '',
                             # der default-Wert ist ein leerer String. Volume sollte mit der Angabe der Nummer des
                             # Bandes der übergeordneten Aufnahme besetzt werden, falls eine übergeordnete Aufnahme
                             # existiert und die Bandzählung nicht nur in Form der Angabe des Publikationsjahres
                             # vorgenommen wird.
                             'volume_year': '',
                             # wird gesetzt, falls die Jahresangabe des Bandes vom Publikationsdatum abweicht.
                             'issue': '',
                             # der default-Wert ist ein leerer String. Issue sollte mit der Angabe der Nummer des
                             # Heftes (NICHT des Bandes) der übergeordneten Aufnahme besetzt werden.
                             'pages': '',
                             # wird belegt, falls Teil einer übergeordneten Aufnahme UND rdamedia = n
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
                             'part_of_series': {'series_title': '', 'part': '', 'uniform_title': ''},
                             # Angabe des Namens und des Teils der Reihe, falls eine Monographie in einer Reihe
                             # erschienen ist. Zusätzlich kann die Zählung der Reihe angegeben werden. Diese wird
                             # inklusive der Angabe Band, Vol. usw. angegeben, falls vorhanden.
                             # als Einheitstitel wird der allgemeine Titel angegeben, falls die Serienteile nicht alle
                             # unter dem selben Serientitel erschienen sind. In Klammern können dahinter
                             # Zusatzinformationen angegeben werden, falls Verwechslungsgefahr mit anderen Serien besteht.
                             'additional_content': {'type': '', 'text': ''},
                             # type MUSS aus der Liste ['Summary', 'Subject', 'Review', 'Scope and content', 'Abstract']
                             # ausgewählt werden.
                             'general_note': '',
                             # allgemeine Anmerkungen
                             'terms_of_access': {'restrictions': False, 'terms_note': '', 'authorized_users': '', 'terms_link': ''},
                             'terms_of_use_and_reproduction': {'terms_note': '', 'use_and_reproduction_rights': '', 'terms_link': ''},
                             # use_and_reproduction_rights taken from a standardized list of terms (e.g., Creative Commons or Rights Statements) indicating the use and reproduction rights
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
                                   }],
                             'edit_names': False,
                             'host_item_is_volume': False}


def add_field_from_record_to_publication_dict(publication_dict, record, field_list):
    for field_nr in field_list:
        for field in record.get_fields(field_nr):
            publication_dict['additional_fields'].append({'tag': field.tag, 'indicators': field.indicators, 'subfields': [subfield.strip('.').strip(' ; ') for subfield in field.subfields]})
    return publication_dict

# Die Funktion übernimmt Felder im ursprünglichen Record, die unverändert bleiben sollen, und fügt diese zum Publication-Dictionary hinzu.


def doi_is_valid(doi):
    if 'doi.org' not in doi:
        doi = 'https://dx.doi.org/' + doi
    doi_page = None
    request_nr = 0
    while not doi_page:
        if request_nr >= 5:
            break
        request_nr += 1
        try:
            req = urllib.request.Request(doi)
            with urllib.request.urlopen(req) as response:
                doi_page = response.read()
            return True
        except Exception as e:
            if request_nr == 4:
                write_error_to_logfile.write(e)
                write_error_to_logfile.comment(doi)
    return False


def link_is_valid(link):
    link_page = None
    request_nr = 0
    while not link_page:
        if request_nr >= 5:
            break
        request_nr += 1
        if 'jstor' in link:
            return True
        try:
            req = urllib.request.Request(link)
            with urllib.request.urlopen(req) as response:
                link_page = response.read()
            return True
        except Exception as e:
            if request_nr == 4:
                write_error_to_logfile.write(e)
                write_error_to_logfile.comment(link)
            continue
    return False


def determine_nonfiling_characters(language, title_dict):
    nonfiling_characters = 0
    if language in language_articles.keys():
        first_word = (title_dict['main_title'].split()[0]).lower()
        if first_word in language_articles[language]:
            nonfiling_characters = len(first_word)+1
    return nonfiling_characters


def create_245_and_246(recent_record, title_dict, author_nr, nonfiling_characters):
    try:
        if title_dict['main_title'] and title_dict['sub_title'] and title_dict['responsibility_statement']:
            recent_record.add_field(Field(tag='245', indicators=[str(author_nr), str(nonfiling_characters)],
                                          subfields=['a', title_dict['main_title'], 'b', title_dict['sub_title'],
                                                     'c', title_dict['responsibility_statement']]))
        elif title_dict['main_title'] and title_dict['sub_title']:
            recent_record.add_field(Field(tag='245', indicators=[str(author_nr), str(nonfiling_characters)],
                                          subfields=['a', title_dict['main_title'], 'b', title_dict['sub_title']]))
        elif title_dict['main_title'] and title_dict['responsibility_statement']:
            recent_record.add_field(Field(tag='245', indicators=[str(author_nr), str(nonfiling_characters)],
                                          subfields=['a', title_dict['main_title'], 'c', title_dict['responsibility_statement']]))
        else:
            recent_record.add_field(Field(tag='245', indicators=[str(author_nr), str(nonfiling_characters)],
                                          subfields=['a', title_dict['main_title']]))
        for parallel_title in title_dict['parallel_titles']:
            recent_record.add_field(Field(tag='246', indicators=['2', '1'],
                                          subfields=['a', parallel_title]))
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment(title_dict)


def create_245_and_246_for_review(recent_record, review_list, author_nr):
    try:
        reviewed_publication_nr = 0
        for reviewed_publication in review_list:
            if reviewed_publication['reviewed_title']:
                responsible = ''
                if reviewed_publication['reviewed_authors']:
                    responsible = reviewed_publication['reviewed_authors'][0] + ': '
                elif reviewed_publication['reviewed_editors']:
                    responsible = reviewed_publication['reviewed_editors'][0] + '(Hrsg.): '
                if reviewed_publication['reviewed_title'] and (reviewed_publication_nr == 0):
                    recent_record.add_field(Field(tag='245', indicators=[str(author_nr), '0'],
                                                  subfields=['a', '[Rez.zu]: ' + responsible + reviewed_publication['reviewed_title']]))
                elif reviewed_publication['reviewed_title']:
                    recent_record.add_field(Field(tag='246', indicators=['1', '3'],
                                                  subfields=['a', '[Rez.zu]: ' + responsible + reviewed_publication['reviewed_title']]))
                reviewed_publication_nr += 1
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment(review_list)


def create_245_and_246_for_response(recent_record, response_list, author_nr):
    try:
        reviewed_publication_nr = 0
        for reviewed_publication in response_list:
            if reviewed_publication['reviewed_title']:
                responsible = ''
                if reviewed_publication['reviewed_authors']:
                    responsible = reviewed_publication['reviewed_authors'][0] + ': '
                elif reviewed_publication['reviewed_editors']:
                    responsible = reviewed_publication['reviewed_editors'][0] + '(Hrsg.): '
                if reviewed_publication['reviewed_title'] and (reviewed_publication_nr == 0):
                    recent_record.add_field(Field(tag='245', indicators=[str(author_nr), '0'],
                                                  subfields=['a', '[Response to]:[Rez.zu]: ' + responsible + reviewed_publication['reviewed_title']]))
                elif reviewed_publication['reviewed_title']:
                    recent_record.add_field(Field(tag='246', indicators=['1', '3'],
                                                  subfields=['a', '[Response to]:[Rez.zu]: ' + responsible + reviewed_publication['reviewed_title']]))
                reviewed_publication_nr += 1
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment(response_list)


def create_title_for_review_and_response_search(review_list, response_list):
    title_list = []
    for reviewed_title in review_list:
        if reviewed_title['reviewed_title']:
            responsible = ''
            if reviewed_title['reviewed_authors']:
                responsible = reviewed_title['reviewed_authors'][0] + ': '
            elif reviewed_title['reviewed_editors']:
                responsible = reviewed_title['reviewed_editors'][0] + ': '
            title_list.append('[Rez.zu]: ' + responsible + reviewed_title['reviewed_title'])
    for response in response_list:
        responsible = ''
        if response['reviewed_authors']:
            responsible = response['reviewed_authors'][0] + ': '
        elif response['reviewed_editors']:
            responsible = response['reviewed_editors'][0] + ': '
        title_list.append('[Rez.zu]: ' + responsible + response['reviewed_title'])
    return title_list


def create_773(recent_record, publication_dict, volume, review, response):
    try:
        if volume and publication_dict['volume_year']:
            location_in_host_item = publication_dict['volume'] \
                                    + ' (' + publication_dict['volume_year'] + ')'
        elif volume:
            location_in_host_item = publication_dict['volume'] \
                                    + ' (' + publication_dict['publication_year'] + ')'
        elif publication_dict['volume_year']:
            location_in_host_item = publication_dict['volume_year']
        else:
            location_in_host_item = publication_dict['publication_year']
        if publication_dict['host_item_is_volume']:
            recent_record.add_field(Field(tag='773', indicators=['0', '8'],
                                          subfields=['w', publication_dict['host_item']['sysnumber'],
                                                     't', publication_dict['host_item']['name'] + ', ' + location_in_host_item]))
        else:
            recent_record.add_field(Field(tag='773', indicators=['0', '8'],
                                          subfields=['w', publication_dict['host_item']['sysnumber'],
                                                     't', publication_dict['host_item']['name'], 'g', location_in_host_item]))
        if publication_dict['host_item']['issn']:
            recent_record['773'].add_subfield('x', publication_dict['host_item']['issn'])

        # wenn die ü.g eine ZS ist, dann sollte $g belegt und $t nur mit dem Titel belegt werden.
        # publication_dict['host_item_is_volume'] = True
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment(publication_dict)


def add_subject_from_additional_physical_form_entry(additional_physical_form_entrys, recent_record, publication_dict):
    try:
        all_par_subjects = {}
        for par in additional_physical_form_entrys:
            webfile = urllib.request.urlopen(
                "https://zenon.dainst.org/Record/" + par['zenon_id'] + "/Export?style=MARC")
            new_reader = MARCReader(webfile)
            for file in new_reader:
                all_par_subjects[par['zenon_id']] = file.get_fields('600', '610', '611', '630', '647', '648', '650', '651') if file.get_fields('600', '610', '611', '630', '647', '648', '650', '651') else {}
            for entry in all_par_subjects:
                for field in all_par_subjects[entry]:
                    if field.tag in ['600', '610', '611', '630', '647', '648', '650', '651']:
                        recent_record.add_field(field)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment(publication_dict)

def check_publication_dict_for_completeness_and_validity(publication_dict):
    try:
        validity = True
        for key in publication_dict_template:
            if key not in publication_dict:
                write_error_to_logfile.comment('Statement ' + key + ' missing in publication dict.')
                print('Statement ' + key + ' missing in publication dict.')
                validity = False
        for key in publication_dict:
            if key not in publication_dict_template:
                write_error_to_logfile.comment('Statement' + key + 'may not appear in publication dict.')
                print('Statement' + key + 'may not appear in publication dict.')
                validity = False
        if not publication_dict['title_dict']['main_title'] and not publication_dict['review'] and not publication_dict['response']:
            write_error_to_logfile.comment('Main title has to be specified.')
            print('Main title has to be specified.')
            validity = False
        for key in publication_dict['title_dict']:
            if type(publication_dict['title_dict'][key]).__name__ != 'str' and key != 'parallel_titles':
                write_error_to_logfile.comment(key.capitalize() + 'has to be of type string but is' + type(publication_dict['title_dict'][key]).__name__ + '.')
                print(key.capitalize() + 'has to be of type string but is' + type(publication_dict['title_dict'][key]).__name__ + '.')
                validity = False
            if key == 'parallel_titles' and type(publication_dict['title_dict'][key]).__name__ != 'list':
                write_error_to_logfile.comment(key.capitalize() + 'has to be of type list but is' + type(publication_dict['title_dict'][key]).__name__ + '.')
                print(key.capitalize() + 'has to be of type list but is' + type(publication_dict['title_dict'][key]).__name__ + '.')
                validity = False
        for responsible_persons_list in ['authors_list', 'editors_list']:
            if type(publication_dict[responsible_persons_list]).__name__ != 'list':
                write_error_to_logfile.comment(responsible_persons_list.capitalize() + 'has to be of type list but is' + type(publication_dict[responsible_persons_list]).__name__ + '.')
                print(responsible_persons_list.capitalize() + 'has to be of type list but is' + type(publication_dict[responsible_persons_list]).__name__ + '.')
                validity = False
        for link in ['abstract_link', 'table_of_contents_link']:
            if publication_dict[link]:
                if type(publication_dict[link]).__name__ != 'str':
                    write_error_to_logfile.comment(link.capitalize() + 'has to be of type string but is' + type(publication_dict[link]).__name__ + '.')
                    print(link.capitalize() + 'has to be of type string but is' + type(publication_dict[link]).__name__ + '.')
                    validity = False
                else:
                    if not link_is_valid(publication_dict[link]):
                        write_error_to_logfile.comment('Link' + publication_dict[link] + 'is not valid.')
                        print('Link' + publication_dict[link] + 'is not valid.')
                        validity = False
        if not publication_dict['pdf_links'] + publication_dict['html_links']:
            if publication_dict['field_007']:
                if publication_dict['field_007'][0:2] == 'cr':
                    if publication_dict['force_epub']:
                        validity = True
                    else:
                        write_error_to_logfile.comment('Records of online resources have to have a link to the online resource.')
                        print('Records of online resources have to have a link to the online resource.')
                        validity = False
        for link in publication_dict['pdf_links'] + publication_dict['html_links']:
            if type(link).__name__ != 'str':
                write_error_to_logfile.comment('Link has to be of type string but is' + type(link).__name__ + '.')
                print('Link has to be of type string but is' + type(link).__name__ + '.')
                validity = False
            else:
                if not link_is_valid(link):
                    write_error_to_logfile.comment('Link' + link + 'is not valid')
                    print('Link' + link + 'is not valid')
                    validity = False
        for link in publication_dict['other_links_with_public_note']:
            if link['url']:
                if type(link['url']).__name__ != 'str':
                    write_error_to_logfile.comment('Link has to be of type string but is' + type(link['url']).__name__ + '.')
                    print('Link has to be of type string but is' + type(link['url']).__name__ + '.')
                    validity = False
                else:
                    if not link_is_valid(link['url']):
                        write_error_to_logfile.comment('Link' + link + 'is not valid')
                        print('Link' + link + 'is not valid')
                        validity = False
                if type(link['public_note']).__name__ != 'str':
                    write_error_to_logfile.comment('Public note has to be of type string but is' + type(link['public_note']).__name__ + '.')
                    print('Public note has to be of type string but is' + type(link['public_note']).__name__ + '.')
                    validity = False
        if publication_dict['doi']:
            if type(publication_dict['doi']).__name__ != 'str':
                write_error_to_logfile.comment('DOI has to be of type string but is' + type(publication_dict['doi']).__name__ + '.')
                print('DOI has to be of type string but is' + type(publication_dict['doi']).__name__ + '.')
                validity = False
            #if not doi_is_valid(publication_dict['doi']):
                #write_error_to_logfile.comment('DOI' + publication_dict['doi'] + 'is not valid')
                #print('DOI' + publication_dict['doi'] + 'is not valid')
                #validity = False
        if publication_dict['urn']:
            if type(publication_dict['urn']).__name__ != 'str':
                write_error_to_logfile.comment('URN has to be of type string but is' + type(publication_dict['doi']).__name__ + '.')
                print('URN has to be of type string but is' + type(publication_dict['urn']).__name__ + '.')
                validity = False
        if publication_dict['isbn']:
            if publication_dict['LDR_06_07'] != 'am':
                write_error_to_logfile.comment('ISBN is only necessary for records of monographs.')
                print('ISBN is only necessary for records of monographs.')
                validity = False
            else:
                if type(publication_dict['isbn']).__name__ != 'str':
                    write_error_to_logfile.comment('ISBN has to be of type string but is' + type(publication_dict['isbn']).__name__ + '.')
                    print('ISBN has to be of type string but is' + type(publication_dict['isbn']).__name__ + '.')
                    validity = False
                else:
                    isbn = publication_dict['isbn'].replace('-', '').replace(' ', '')
                    if re.findall(r'[^\d]', isbn):
                        write_error_to_logfile.comment('ISBN has to contain nothing but digits and separators.')
                        print('ISBN has to contain nothing but digits and separators.')
                        validity = False
                    if len(isbn) not in [10, 13]:
                        write_error_to_logfile.comment('ISBN without seperators has to consist of either 10 or 13 digits.')
                        print('ISBN without seperators has to consist of either 10 or 13 digits.')
                        validity = False
        if publication_dict['fields_590']:
            if type(publication_dict['fields_590']).__name__ != 'list':
                write_error_to_logfile.comment('fields_590 has to be of type list but is' + type(publication_dict['fields_590']).__name__ + '.')
                print('fields_590 has to be of type list but is', type(publication_dict['fields_590']).__name__ + '.')
                validity = False
            else:
                for field in publication_dict['fields_590']:
                    if type(field).__name__ != 'str':
                        write_error_to_logfile.write('field_590 has to be of type string but is' + type(field).__name__ + '.')
                        print('field_590 has to be of type string but is', type(field).__name__ + '.')
                        validity = False
        if publication_dict['original_cataloging_agency']:
            if type(publication_dict['original_cataloging_agency']).__name__ != 'str':
                write_error_to_logfile.comment('Original_cataloging_agency has to be of type string but is' + type(publication_dict['original_cataloging_agency']).__name__ + '.')
                print('Original_cataloging_agency has to be of type string but is', type(publication_dict['original_cataloging_agency']).__name__ + '.')
                validity = False
        if publication_dict['publication_year']:
            if type(publication_dict['publication_year']).__name__ != 'str':
                write_error_to_logfile.comment('publication_year has to be of type string but is' + type(publication_dict['publication_year']).__name__ + '.')
                print('publication_year has to be of type string but is', type(publication_dict['publication_year']).__name__ + '.')
                validity = False
            if not (re.findall(r'\d{4}', publication_dict['publication_year']) and (len(publication_dict['publication_year']) == 4)):
                write_error_to_logfile.comment('publication_year has to consist of four digits.')
                print('publication_year has to consist of four digits.')
                validity = False
        if publication_dict['field_300']:
            if type(publication_dict['field_300']).__name__ != 'str':
                write_error_to_logfile.comment('field_300 has to be of type string but is' + type(publication_dict['publication_year']).__name__ + '.')
                print('field_300 has to be of type string but is', type(publication_dict['publication_year']).__name__ + '.')
                validity = False
        for statement in publication_dict['publication_etc_statement']:
            if publication_dict['publication_etc_statement'][statement]['country_code']:
                if len(publication_dict['publication_etc_statement'][statement]['country_code']) != 3:
                    print('Country_code has to consist of three characters including whitespaces.')
                    write_error_to_logfile.comment('Country_code has to consist of three characters including whitespaces.')
                    validity = False
        if publication_dict['copyright_year']:
            if type(publication_dict['copyright_year']).__name__ != 'str':
                print('copyright_year has to be of type string but is', type(publication_dict['copyright_year']).__name__ + '.')
                write_error_to_logfile.comment('copyright_year has to be of type string but is' + type(publication_dict['copyright_year']).__name__ + '.')
                validity = False
            if not re.findall(r'\d{4}', publication_dict['copyright_year']):
                print('copyright_year has to consist of four digits.')
                write_error_to_logfile.comment('copyright_year has to consist of four digits.')
                validity = False
        if not publication_dict['rdacontent']:
            print('rdacontent has to be specified.')
            write_error_to_logfile.comment('rdacontent has to be specified.')
            validity = False
        else:
            if publication_dict['rdacarrier'] not in rda_codes['rdacarrier']:
                print('Code for rdacarrier is not valid.')
                write_error_to_logfile.comment('Code for rdacarrier is not valid.')
                validity = False
            elif publication_dict['rdacarrier'] == 'cr':
                if publication_dict['rdamedia'] != 'c':
                    print('If rdacarrier is "cr", rdamedia has to be "c".')
                    write_error_to_logfile.comment('If rdacarrier is "cr", rdamedia has to be "c".')
                    validity = False
                if publication_dict['field_007'][0:2] != 'cr':
                    print('If rdacarrier is "cr", field_007 has to be "cr".')
                    write_error_to_logfile.comment('If rdacarrier is "cr", field_007 has to be "cr".')
                    validity = False
                if publication_dict['LDR_06_07'][0] != 'm':
                    if not publication_dict['field_006']:
                        print('If rdacarrier is "cr" and LDR_06_07 is not "m", field_006 has to be specified.')
                        write_error_to_logfile.comment('If rdacarrier is "cr" and LDR_06_07 is not "m", field_006 has to be specified.')
                        validity = False
            elif publication_dict['rdacarrier'] == 'nc':
                if publication_dict['rdamedia'] != 'n':
                    print('If rdacarrier is "nc", rdamedia has to be "n".')
                    write_error_to_logfile.comment('If rdacarrier is "nc", rdamedia has to be "n".')
                    validity = False
                if publication_dict['field_007'][0:2] != 'ta':
                    print('If rdacarrier is "nc", field_007 has to be "ta".')
                    write_error_to_logfile.comment('If rdacarrier is "nc", field_007 has to be "ta".')
                    validity = False
            elif not publication_dict['rdamedia']:
                print('rdamedia has to be specified.')
                write_error_to_logfile.comment('rdamedia has to be specified.')
                validity = False
        if not publication_dict['rdacarrier']:
            print('rdacarrier has to be specified.')
            write_error_to_logfile.comment('rdacarrier has to be specified.')
            validity = False
        if publication_dict['rdacontent'] == 'txt':
            if publication_dict['LDR_06_07'][0] != 'a':
                print('If rdacontent ist "txt", first letter of "LDR_06_07" has to be "a".')
                write_error_to_logfile.comment('If rdacontent ist "txt", first letter of "LDR_06_07" has to be "a".')
                validity = False
        if publication_dict['LDR_06_07'][1] in ['a', 'b']:
            if not (publication_dict['host_item']['sysnumber'] or publication_dict['host_item']['name']):
                print('If resource is monographic component part or serial component part, host_item has to be specified.')
                write_error_to_logfile.comment('If resource is monographic component part or serial component part, host_item has to be specified.')
                validity = False
        if len(publication_dict['LDR_06_07']) != 2:
            print('LDR_06_07 has to consist of two characters.')
            write_error_to_logfile.comment('LDR_06_07 has to consist of two characters.')
            validity = False
        if len(publication_dict['field_008_18-34']) != 17:
            print('field_008_18-34 has to consist of 17 characters.')
            write_error_to_logfile.comment('field_008_18-34 has to consist of 17 characters.')
            validity = False
        if publication_dict['language_field']["language_of_resource"] and publication_dict['language_field']["language_of_original_item"]:
            if len(publication_dict['language_field']["language_of_resource"]) != 3:
                print('Language of resource has to consist of three characters.')
                write_error_to_logfile.comment('Language of resource has to consist of three characters.')
                validity = False
            if len(publication_dict['language_field']["language_of_original_item"]) != 3:
                print('Language of original item has to consist of three characters.')
                write_error_to_logfile.comment('Language of original item has to consist of three characters.')
                validity = False
        if publication_dict['part_of_series']:
            if publication_dict['part_of_series']['series_title']:
                if publication_dict['LDR_06_07'][1] != 'm':
                    print('Specification of information about series is only permitted if resource is monograph.')
                    write_error_to_logfile.comment('Specification of information about series is only permitted if resource is monograph.')
                    validity = False
        if publication_dict['additional_content']:
            if publication_dict['additional_content']['type']:
                if publication_dict['additional_content']['type'] not in ['Summary', 'Subject', 'Review', 'Scope and content', 'Abstract']:
                    print('Type of additional content has to be in [Summary, Subject, Review, Scope and content, Abstract].')
                    write_error_to_logfile.comment('Type of additional content has to be in [Summary, Subject, Review, Scope and content, Abstract].')
                    validity = False
        return validity
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment(publication_dict)


def create_new_record(out, publication_dict):
    created = 0
    try:
        for review_entry in publication_dict['review_list']:
            if not review_entry['reviewed_title']:
                publication_dict['review_list'].remove(review_entry)
        if publication_dict['review'] or publication_dict['response']:
            publication_dict['title_dict']['main_title'] = create_title_for_review_and_response_search(publication_dict['review_list'], publication_dict['response_list'])[0]
            all_doublets, additional_physical_form_entrys = \
                find_existing_doublets.find_review([person.split(', ')[0] for person in (publication_dict['authors_list'] + publication_dict['editors_list'])],
                                            publication_dict['publication_year'], 'en', [publication_dict['host_item']['sysnumber']], publication_dict)
        else:
            print([publication_dict['host_item']['sysnumber']])
            all_doublets, additional_physical_form_entrys = \
                find_existing_doublets.find((publication_dict['title_dict']['main_title']+' '+str(publication_dict['title_dict']['sub_title'])).replace('None', '').strip(),
                                            [person.split(', ')[0] for person in (publication_dict['authors_list'] + publication_dict['editors_list'])],
                                            publication_dict['publication_year'], 'en', [publication_dict['host_item']['sysnumber']], publication_dict)
        if all_doublets:
            print('doublet found:', list(set(all_doublets)))
            # print(publication_dict['title_dict'])
            # print(publication_dict['authors_list'], publication_dict['editors_list'], publication_dict['publication_year'])
        elif additional_physical_form_entrys:
            print('additional physical form entry', additional_physical_form_entrys)
            print(publication_dict['title_dict'])
            print(publication_dict['authors_list'], publication_dict['editors_list'], publication_dict['publication_year'])
        if not all_doublets:
            recent_record = Record(force_utf8=True)
            recent_record.leader = \
                recent_record.leader[:5] + 'n' + publication_dict['LDR_06_07'] + ' a22     uu ' + recent_record.leader[20:]
            if publication_dict['field_006']:
                recent_record.add_field(Field(tag='006', indicators=None, data=publication_dict['field_006']))
            recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=publication_dict['field_007']))
            language = 'und'
            if publication_dict['text_body_for_lang_detection']:
                if len(re.findall(r'\w', publication_dict['text_body_for_lang_detection'])) >= 50:
                    try:
                        language = \
                            language_codes.resolve(detect(publication_dict['text_body_for_lang_detection']))
                    except:
                        language = 'und'
            if language == 'und':
                try:
                    language = language_codes.resolve(detect(' '.join([publication_dict['title_dict']['main_title'], publication_dict['title_dict']['sub_title']])))
                except:
                    language = 'und'
            if not publication_dict['do_detect_lang']:
                if len(publication_dict['default_language']) == 3:
                    language = publication_dict['default_language']
                else:
                    language = language_codes.resolve(publication_dict['default_language'])
            second_indicators = ['3', '2', '0', '1']
            function_nr = 0
            country_code = 'xx '
            for function in ['manufacture', 'distribution', 'production', 'publication']:
                if publication_dict['publication_etc_statement'][function]['place']:
                    recent_record.add_field(Field(tag='264', indicators=[' ', second_indicators[function_nr]],
                                                  subfields=[
                                                      'a', publication_dict['publication_etc_statement'][function]['place'],
                                                      'b', publication_dict['publication_etc_statement'][function]['responsible'],
                                                      'c', publication_dict['publication_year']]))
                    country_code = publication_dict['publication_etc_statement'][function]['country_code']
                function_nr += 1
            if publication_dict['copyright_year'] and publication_dict['copyright_year'] != publication_dict['publication_year']:
                recent_record.add_field(Field(tag='264', indicators=[' ', '4'],
                                              subfields=['c', '©' + publication_dict['copyright_year']]))
            time = str(arrow.now().format('YYMMDD'))
            if publication_dict['retro_digitization_info']['date_published_online']:
                publication_dict['field_008_06'] = 'r'
                first_date = publication_dict['retro_digitization_info']['date_published_online']
                second_date = publication_dict['publication_year']
            elif publication_dict['copyright_year'] and publication_dict['copyright_year'] != publication_dict['publication_year']:
                publication_dict['field_008_06'] = 't'
                first_date = publication_dict['publication_year']
                second_date = publication_dict['copyright_year']
            else:
                publication_dict['field_008_06'] = 's'
                first_date = publication_dict['publication_year']
                second_date = '    '
            if publication_dict['review'] and publication_dict['field_008_18-34'] == ' ':
                publication_dict['field_008_18-34'] = publication_dict['field_008_18-34'][:8] + 'o  ' + publication_dict['field_008_18-34'][11:]
            data_008 = time + publication_dict['field_008_06'] + first_date + second_date + \
                country_code + publication_dict['field_008_18-34'] + language + ' d'
            recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
            if publication_dict['isbn']:
                recent_record.add_field(Field(tag='020', indicators=[' ', ' '],
                                              subfields=['a', publication_dict['isbn']]))
            if publication_dict['doi']:
                recent_record.add_field(Field(tag='024', indicators=['7', ' '],
                                              subfields=['a', publication_dict['doi'], '2', 'doi']))
            if publication_dict['urn']:
                recent_record.add_field(Field(tag='024', indicators=['7', ' '],
                                              subfields=['a', publication_dict['urn'], '2', 'urn']))
            recent_record.add_field(Field(tag='040', indicators=[' ', ' '],
                                          subfields=['a', publication_dict['original_cataloging_agency'],
                                                     'b', 'eng', 'd', 'DE-2553', 'e', 'rda']))
            if publication_dict['language_field']['language_of_resource']:
                subfields = [y for publication_dict['language_field']['language_of_resource'] in publication_dict['language_field']['language_of_resource'] for y in
                             ['language_of_resource', publication_dict['language_field']['language_of_resource']]] + ['h', publication_dict['language_field']['language_of_original_item']]
                recent_record.add_field(Field(tag='041', indicators=[str(int(bool(publication_dict['language_field']['language_of_original_item']))), ' '], subfields=subfields))
            author_nr = 0
            if publication_dict['authors_list']:
                for author in publication_dict['authors_list']:
                    if author_nr == 0:
                        recent_record.add_field(Field(tag='100', indicators=['1', ' '], subfields=['a', author]))
                        author_nr += 1
                    else:
                        recent_record.add_field(Field(tag='700', indicators=['1', ' '], subfields=['a', author]))
            elif publication_dict['editors_list']:
                for author in publication_dict['editors_list']:
                    if author_nr == 0:
                        recent_record.add_field(Field(tag='100', indicators=['1', ' '], subfields=['a', author]))
                        author_nr += 1
                    else:
                        recent_record.add_field(Field(tag='700', indicators=['1', ' '], subfields=['a', author]))
            if publication_dict['review']:
                create_245_and_246_for_review(recent_record, publication_dict['review_list'], author_nr)
            elif publication_dict['response']:
                create_245_and_246_for_response(recent_record, publication_dict['response_list'], author_nr)
            else:
                create_245_and_246(recent_record, publication_dict['title_dict'],
                                   author_nr, determine_nonfiling_characters(language, publication_dict['title_dict']))
            if publication_dict['force_300'] == True:
                recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', publication_dict['field_300']]))
            elif publication_dict['rdacarrier'] == 'cr':
                recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', '1 online resource']))
            elif publication_dict['pages'] and publication_dict['issue']:
                recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', 'Fasc. ' + publication_dict['issue'] + ', '+publication_dict['pages']]))
            elif publication_dict['pages']:
                recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', publication_dict['pages']]))
            elif publication_dict['issue']:
                recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', 'Fasc. ' + publication_dict['issue']]))
            else:
                recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', publication_dict['field_300']]))
            # was ist mit pages
            recent_record.add_field(Field(tag='336', indicators=[' ', ' '],
                                          subfields=['a', rda_codes['rdacontent'][publication_dict['rdacontent']],
                                                     'b', publication_dict['rdacontent'], '2', 'rdacontent']))
            recent_record.add_field(Field(tag='337', indicators=[' ', ' '],
                                          subfields=['a', rda_codes['rdamedia'][publication_dict['rdamedia']],
                                                     'b', publication_dict['rdamedia'], '2', 'rdamedia']))
            recent_record.add_field(Field(tag='338', indicators=[' ', ' '],
                                          subfields=['a', rda_codes['rdacarrier'][publication_dict['rdacarrier']],
                                                     'b', publication_dict['rdacarrier'], '2', 'rdacarrier']))
            if publication_dict['part_of_series']['series_title']:
                recent_record.add_field(Field(tag='490', indicators=['1', ' '],
                                              subfields=['a', publication_dict['part_of_series']['series_title'],
                                                         'v', publication_dict['part_of_series']['part']]))
                if publication_dict['part_of_series']['uniform_title']:
                    recent_record.add_field(Field(tag='830', indicators=[' ', '0'],
                                                  subfields=['a', publication_dict['part_of_series']['uniform_title'],
                                                             'v', publication_dict['part_of_series']['part']]))
                else:
                    recent_record.add_field(Field(tag='830', indicators=[' ', '0'],
                                                  subfields=['a', publication_dict['part_of_series']['series_title'],
                                                             'v', publication_dict['part_of_series']['part']]))
            if publication_dict['general_note']:
                recent_record.add_field(Field(tag='500', indicators=[' ', ' '], subfields=['a', publication_dict['general_note']]))
            if publication_dict['retro_digitization_info']['publisher']:
                recent_record.add_field(Field(tag='533', indicators=[' ', ' '],
                                        subfields=['a', 'Online edition', 'b', publication_dict['retro_digitization_info']['place_of_publisher'],
                                                   'c', publication_dict['retro_digitization_info']['publisher'], 'd', publication_dict['retro_digitization_info']['date_published_online'],
                                                   'e', 'Online resource']))
            if publication_dict['terms_of_access']['terms_note']:
                if publication_dict['terms']['terms_link']:
                    recent_record.add_field(Field(tag='506', indicators=[str(int(publication_dict['terms_of_access']['restrictions'])), ' '],
                                                  subfields=['a', publication_dict['terms_of_access']['terms_note'],
                                                             'd', publication_dict['terms_of_access']['authorized_users'],
                                                             'u', publication_dict['terms_of_access']['terms_link']]))
                else:
                    recent_record.add_field(Field(tag='506', indicators=[str(int(publication_dict['terms_of_access']['restrictions'])), ' '],
                                                  subfields=['a', publication_dict['terms_of_access']['terms_note'],
                                                             'd', publication_dict['terms_of_access']['authorized_users']]))
            if publication_dict['additional_content']['type']:
                type_list = ['Summary', 'Subject', 'Review', 'Scope and content', 'Abstract']
                if publication_dict['additional_content']['type'] in type_list:
                    recent_record.add_field(Field(tag='520', indicators=[type_list.index(publication_dict['additional_content']['type'])-1
                                                                         if type_list.index(publication_dict['additional_content']['type']) > 0 else ' ', ' '],
                                                  subfields=['a', publication_dict['additional_content']['text']]))
            if publication_dict['terms_of_use_and_reproduction']['terms_note']:
                if publication_dict['terms_of_use_and_reproduction']['terms_link'] and publication_dict['terms_of_use_and_reproduction']['use_and_reproduction_rights']:
                    recent_record.add_field(Field(tag='540', indicators=[' ', ' '],
                                                  subfields=['a', publication_dict['terms_of_use_and_reproduction']['terms_note'],
                                                             'f', publication_dict['terms_of_use_and_reproduction']['use_and_reproduction_rights'],
                                                             'u', publication_dict['terms_of_use_and_reproduction']['terms_link']]))
                elif publication_dict['terms_of_use_and_reproduction']['terms_link']:
                    recent_record.add_field(Field(tag='540', indicators=[' ', ' '],
                                                  subfields=['a', publication_dict['terms_of_use_and_reproduction']['terms_note'],
                                                             'u', publication_dict['terms_of_use_and_reproduction']['terms_link']]))
                elif publication_dict['terms_of_use_and_reproduction']['use_and_reproduction_rights']:
                    recent_record.add_field(Field(tag='540', indicators=[' ', ' '],
                                                  subfields=['a', publication_dict['terms_of_use_and_reproduction']['terms_note'],
                                                             'f', publication_dict['terms_of_use_and_reproduction']['use_and_reproduction_rights']]))
            for field_590 in publication_dict['fields_590']:
                recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', field_590]))
            if publication_dict['abstract_link']:
                if len(re.findall(r'\w', publication_dict['text_body_for_lang_detection'])) >= 50:
                    recent_record.add_field(Field(tag='856', indicators=['4', '2'],
                                                  subfields=['z', 'Abstract', 'u', publication_dict['abstract_link']]))
            if publication_dict['table_of_contents_link']:
                recent_record.add_field(Field(tag='856', indicators=['4', '2'],
                                              subfields=['z', 'Table of Contents', 'u', publication_dict['table_of_contents_link']]))
            print(publication_dict['pdf_links'] + publication_dict['html_links'])
            for link in publication_dict['pdf_links']:
                recent_record.add_field(Field(tag='856', indicators=['4', '0'],
                                              subfields=['z', 'Available online', 'u', link]))
            for link in publication_dict['html_links']:
                recent_record.add_field(Field(tag='856', indicators=['4', '0'],
                                              subfields=['z', 'Available online', 'u', link]))
            for link in publication_dict['other_links_with_public_note']:
                if link['url']:
                    recent_record.add_field(Field(tag='856', indicators=['4', '2'],
                                                  subfields=['z', link['public_note'], 'u', link['url']]))
            if publication_dict['host_item']['sysnumber']:
                create_773(recent_record, publication_dict, publication_dict['volume'], publication_dict['review'], publication_dict['response'])
            for additional_physical_form_entry in additional_physical_form_entrys:
                recent_record.add_field(Field(tag='776', indicators=['0', '8'],
                                              subfields=['i', additional_physical_form_entry['subfield_i'], 't', recent_record['245']['a'].strip(' / ').strip(' : '), 'w',
                                                         '(DE-2553)' + additional_physical_form_entry['zenon_id']]))
            for field in publication_dict['additional_fields']:
                if field['data']:
                    recent_record.add_field(Field(tag=field['tag'], data=field['data']))
                elif field['tag']:
                    if field['tag'] == '300':
                        recent_record.remove_fields('300')
                    recent_record.add_field(Field(tag=field['tag'], indicators=field['indicators'],
                                                  subfields=field['subfields']))
            if publication_dict['review']:
                print(publication_dict['review_list'])
                for reviewed_title in publication_dict['review_list']:
                    if reviewed_title['reviewed_title']:
                        reviewed_title_ids, review_titles = find_reviewed_title.find(reviewed_title, publication_dict['publication_year'], 'en')
                        if reviewed_title_ids:
                            print(reviewed_title_ids)
                        else:
                            print('no lkr generated')
                        for reviewed_title_id in reviewed_title_ids:
                            # print(publication_dict['review_list'])
                            # print(reviewed_title_ids)
                            recent_record.add_field(Field(tag='787', indicators=['0', '8'],
                                                          subfields=['w', reviewed_title_id,
                                                                     't', review_titles[reviewed_title_ids.index(reviewed_title_id)][0]]))
            if publication_dict['response']:
                for reviewed_title in publication_dict['response_list']:
                    if reviewed_title['reviewed_title']:
                        reviewed_title_ids, review_titles = find_reviewed_title.find(reviewed_title, publication_dict['publication_year'], 'en')
                        for reviewed_title_id in reviewed_title_ids:
                            recent_record.add_field(Field(tag='787', indicators=['0', '8'],
                                                         subfields=['w', reviewed_title_id,
                                                                    't', publication_dict['title_dict']['main_title'][0]]))

            if additional_physical_form_entrys:
                add_subject_from_additional_physical_form_entry(additional_physical_form_entrys, recent_record, publication_dict)
            print(recent_record)
            out.write(recent_record.as_marc21())
            created = 1
        return created
    except Exception as e:
        write_error_to_logfile.write(e)


''' years_published_in = [int(year) for year in list(publishers.keys())]
    years_published_in.sort(reverse=True)
    years_produced_in = [int(producer_key) for producer_key in list(producers.keys())]
    years_produced_in.sort(reverse=True)
    place_of_publication = ''
    place_of_production = ''
    publisher = ''
    producer = ''
    for key in years_published_in:
        if int(publication_dict['publication_year']) >= key:
            place_of_publication = publishers[str(key)][0]
            publisher = publishers[str(key)][1]
            break
    for key in years_produced_in:
        if int(volume) >= key:
            place_of_production = producers[str(key)][0]
            production = producers[str(key)][1]
            break         
            '''

# falls verschiedene Publikationsangaben berücksichtigt werden sollen.


# Umgang mit Körperschaften

subject_added_entries = [{'type': '', 'text': '', 'source': ''}]
# type MUSS aus der Liste ['Person', 'Corporation', 'Event', 'Chronology', 'Topic', 'Geography']
# source wird mit dem Code für den verwendeten Thesaurus angegeben, falls dieser in
# https://www.loc.gov/standards/sourcelist/subject.html angegeben wird.
# 6**-Felder auch einfügen.
'''
persons = []
for person in persons:
    recent_record.add_field(Field(tag='600', indicators=[first_indicator, '7'],
                                  subfields=['a', person_name, '2', person_authority]))
corporations = []
for corporation in corporations:
    corporation_name = corporation.find('mods:displayForm').text
    corporation_authority = corporation['authority']
    recent_record.add_field(Field(tag='610', indicators=['2', '7'],
                                  subfields=['a', corporation_name, '2', corporation_authority]))
geographics = []
for geographic in geographics:
    geographic_name = geographic.text
    geographic_authority = geographic['authority']
    recent_record.add_field(Field(tag='651', indicators=[' ', '7'],
                                  subfields=['a', geographic_name, '2', geographic_authority]))
topics = []
for topic in topics:
    topic_name = topic.text
    topic_authority = topic['authority']
    recent_record.add_field(Field(tag='650', indicators=[' ', '7'],
                                  subfields=['a', topic_name, '2', topic_authority]))
'''
