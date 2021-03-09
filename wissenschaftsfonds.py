import urllib.parse, urllib.request
from bs4 import BeautifulSoup
import json
import re
import write_error_to_logfile
from harvest_records import harvest_records
from pymarc import MARCReader


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    all_subjects = []
    try:
        current_item = 0
        number = 0
        found = 0
        while number < 1500:
            url = 'https://e-book.fwf.ac.at/detail/o:' + str(number)
            number += 1
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                titles_page = response.read()
            titles_page = titles_page.decode('utf-8')
            titles_soup = BeautifulSoup(titles_page, 'html.parser')
            # if titles_soup.find('div', class_="jumbotron-container jumbotron-alert").text.strip() == 'Dieses Objekt ist nicht aktiv.'
            if titles_soup.find('div', class_="jumbotron-container jumbotron-alert"):
                continue
            found += 1
            dc_url = titles_soup.find('li', class_="help_3408").find('a')['href']
            req = urllib.request.Request(dc_url)
            with urllib.request.urlopen(req) as response:
                book_page = response.read()
            book_page = book_page.decode('utf-8')
            book_soup = BeautifulSoup(book_page, 'xml')
            if book_soup.find('dc:type').text in ['Sound', 'InteractiveResource', 'Collection', 'MovingImage', 'Dataset']:
                continue
            with open('publication_dict.json', 'r') as publication_dict_template:
                publication_dict = json.load(publication_dict_template)
                publication_dict['default_language'] = 'ger' if book_soup.find('dc:language').text=='deu' else book_soup.find('dc:language').text
                publication_dict['do_detect_lang'] = False
                publication_dict['authors_list'] = [tag.text for tag in book_soup.find_all('dc:creator')]
                title_list = book_soup.find('dc:title').text.split(': ', 1)
                if len(title_list) == 1:
                    publication_dict['title_dict']['main_title'] = book_soup.find('dc:title').text
                else:
                    publication_dict['title_dict']['main_title'], publication_dict['title_dict']['sub_title'] = title_list
                publication_dict['abstract_link'] = url
                publication_dict['table_of_contents_link'] = url
                publication_dict['fields_590'] = ['Online publication', '2021xhnxwifok', 'ebookoa0520']
                publication_dict['original_cataloging_agency'] = 'FWF Der Wissenschaftsfonds'
                pos_isbn_list = [re.findall(r'[\d|-]+', tag.text) for tag in book_soup.find_all('dc:identifier') if 'http' not in tag.text][0] if [tag.text.strip('ISBN: ') for tag in book_soup.find_all('dc:identifier') if 'http' not in tag.text] else []
                publication_dict['isbn'] = [num for num in pos_isbn_list if len(re.findall(r'\d{1}', num)) in [10, 13]][0] \
                    if [num for num in pos_isbn_list if len(re.findall(r'\d{1}', num)) in [10, 13]] else ''
                publication_dict['html_links'].append(url)
                publication_dict["force_300"] = False
                publication_dict['rdacarrier'] = 'cr'
                publication_dict['rdamedia'] = 'c'
                publication_dict['rdacontent'] = 'txt'
                publication_dict['LDR_06_07'] = 'am'
                publication_dict['field_007'] = 'cr uuu|||uuuuu'
                publication_dict['field_008_18-34'] = '||||fo|||||||| 0|'
                publication_dict['field_006'] = 'm||||fo|||||||| 0|'
                publication_dict['publication_year'] = re.findall(r'\d{4}', book_soup.find('dc:date').text)[0] if book_soup.find('dc:date') else ''
                rights = [tag.text for tag in book_soup.find_all('dc:rights') if 'CC' in tag.text]
                rights_url = [tag.text for tag in book_soup.find_all('dc:rights') if 'http' in tag.text]
                publication_dict["terms_of_use_and_reproduction"] = {"terms_note": "", "use_and_reproduction_rights": "", "terms_link": ""}
                for subject in [sub.text[11:] for sub in book_soup.find_all('dc:subject', attrs={'xml:lang':"deu"}) if 'ÖFOS' in sub.text]:
                    publication_dict['additional_fields'].append({"tag": "650", "indicators": [" ", "4"], "subfields": ['a', subject], "data":  ""})
                uw_metadata_url = titles_soup.find('li', class_="help_3409").find('a')['href']
                req = urllib.request.Request(uw_metadata_url)
                with urllib.request.urlopen(req) as response:
                    book_page = response.read()
                book_page = book_page.decode('utf-8')
                book_soup = BeautifulSoup(book_page, 'xml')
                if dc_url == 'https://services.e-book.fwf.ac.at/api/object/o:1146/index/dc':
                    publisher = 'Verlag der Österreichischen Akademie der Wissenschaften'
                else:
                    publisher = book_soup.find('ns12:publisher').text
                publisher_location = book_soup.find('ns12:publisherlocation').text if book_soup.find('ns12:publisherlocation') else 'Wien'
                publication_dict['field_300'] = '1 online ressource, ' + book_soup.find('ns12:pagination').text if book_soup.find('ns12:pagination') else '1 online ressource'
                publication_dict['publication_etc_statement']['publication'] = {'place': publisher_location, 'responsible': publisher, 'country_code': 'au '}
                if book_soup.find('ns12:reihentitel') and book_soup.find('ns12:volume'):
                    publication_dict["part_of_series"] = \
                        {"series_title": book_soup.find('ns12:reihentitel').text,
                         "part": book_soup.find('ns12:volume').text,
                         "uniform_title": book_soup.find('ns12:reihentitel').text}
                publication_dicts.append(publication_dict)
                items_harvested.append(current_item)
        print(list(set(all_subjects)))
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Wissenschaftsfonds geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'wifo', 'wifo', create_publication_dicts)
    return return_string

def filter_subjects(subject_list):
    filestring = 'records/wifo/wifo_08-Jun-2020'
    found = 0
    no_subjects = 0
    out = open('records/wifo/filtered_subjects.mrc', 'wb')
    num = 0
    while num <= 525:
        with open(filestring + '_' + str(num) + '.mrc', 'rb') as file:
            new_reader = MARCReader(file)
            for record in new_reader:
                if record.get_fields('650'):
                    subjects_matching = [field['a'] for field in record.get_fields('650') if field['a'] in subject_list]
                    if subjects_matching:
                        out.write(record.as_marc21())
                        found += 1
                else:
                    out.write(record.as_marc21())
                    no_subjects += 1
        num += 25
    print(found)
    print(no_subjects)


if __name__ == '__main__':
    # harvest_records('records/wifo/', 'wifo', 'wifo', create_publication_dicts)
    subject_list = ["Kunstwissenschaften",
                    "Ästhetik",
                    "Restaurierung, Konservierung",
                    "Gräzistik",
                    "Geschichtswissenschaft",
                    "Kulturgeschichte",
                    "Baukunst",
                    "Paläographie, Handschriftenkunde",
                    "Literaturwissenschaft (auch: vergleichende -)",
                    "Ethnologie",
                    "Keltologie",
                    "Sprach- und Literaturwissenschaften",
                    "Archäologie",
                    "Orientalistik",
                    "Altertumskunde",
                    "Ägyptologie",
                    "Historische Hilfswissenschaften",
                    "Ethnologie / Völkerkunde",
                    "Paläontologie",
                    "Klassische Archäologie",
                    "Historische Wissenschaften",
                    "Urgeschichte",
                    "Paläographie",
                    "Sedimentologie",
                    "Europäische Ethnologie / Volkskunde",
                    "Frühgeschichte",
                    "Archäometrie",
                    "Geschichtliche Landeskunde",
                    "Numismatik",
                    "Mittelalterliche Geschichte",
                    "Ethnographie",
                    "Geschichte, Archäologie",
                    "Klassische Philologie",
                    "Byzantinistik",
                    "Kulturgeographie",
                    "Kulturwissenschaft",
                    "Alte Geschichte",
                    "Kulturanthropologie",
                    "Denkmalpflege",
                    "Architekturgeschichte",
                    "Epigraphik",
                    "Indogermanistik"]
    filter_subjects(subject_list)
