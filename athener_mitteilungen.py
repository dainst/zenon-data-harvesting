import urllib.request, urllib.parse
import json
import urllib.parse, urllib.request
from harvest_records import harvest_records
from bs4 import BeautifulSoup
import write_error_to_logfile
import re
import find_sysnumbers_of_volumes


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publishers = {'1876': ['Athen', 'In Commission bei Karl Wilberg'],
                  '1886': ['Athen', 'Verlag Karl Wilberg'],
                  '1896': ['Athen', 'Barth & von Hirst'],
                  '1901': ['Athen', 'Beck und Barth'],
                  '1910': ['Athen', 'Eleutheroudakis und Barth'],
                  '1915': ['Athen', 'Archäologisches Institut'],
                  '1916': ['Berlin', 'Archäologisches Institut'],
                  '1926': ['Athen', 'Archäologisches Institut'],
                  '1938': ['Stuttgart', 'Verlag W. Kohlhammer'],
                  '1942': ['Berlin', 'Walter de Gruyter'],
                  '1953': ['Berlin', 'Verlag Gebr. Mann'],
                  '1997': ['Mainz', 'Philipp von Zabern'],
                  '2011': ['Berlin', 'Verlag Gebr. Mann']
                  }
    years_published_in = [int(year) for year in list(publishers.keys())]
    years_published_in.sort(reverse=True)
    titles_for_supplementing = ['Sitzungsprotocolle', 'Sitzungs-Protocolle', 'Litteratur und Funde',
                                'Ernennungen', 'Eingegangene Schriften', 'Miscellen', 'Litteratur',
                                'Berichtigungen', 'Epigraphische Miscellen', 'Funde', 'Sitzungsprotokolle',
                                'Ernennungen / Sitzungs-Protocolle', 'Register']
    publication_dicts = []
    items_harvested = []
    try:
        sysnumbers = find_sysnumbers_of_volumes.find_sysnumbers('000054834')
        sysnumbers['1883'] = '001101806'
        sysnumbers['1888'] = '001101811'
        basic_url = 'https://digi.ub.uni-heidelberg.de/diglit/am'
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
            yearbook_page = response.read()
        yearbook_page = yearbook_page.decode('utf-8')
        yearbook_page = BeautifulSoup(yearbook_page, 'html.parser')
        volume_years = [item.text for item in yearbook_page.find('table', class_='tabelle-baendeliste').find_all('span', class_='publ-daten-schwarz')]
        volume_urls = [item['href'] for item in yearbook_page.find('table', class_='tabelle-baendeliste').find_all('a')]
        for volume_url in volume_urls:
            print(volume_url)
            volume_year=volume_years[record_nr].split('(')[0].split(', ')[-1]
            record_nr+=1
            mets_url=volume_url.split("?")[0]+'/mets'
            print(mets_url)
            webFile = urllib.request.urlopen(mets_url)
            xml_soup=BeautifulSoup(webFile, 'xml')
            date_of_publication = xml_soup.find_all('mods:mods')[0].find('mods:originInfo').find('mods:dateIssued', keyDate='yes').text
            if '(' in date_of_publication:
                date_of_publication = date_of_publication.split('(')[1].replace(')')
            volume=xml_soup.find_all('mods:mods')[0].find('mods:number').text
            content_tags = [tag.find('mods:mods') for tag in xml_soup.find_all('mets:dmdSec')if re.findall(r'^dmd\d+$', tag['ID'])]
            for item in content_tags:
                current_item = int(volume_year)
                if current_item == 1888:
                    continue
                if not item.find('mods:identifier', type='doi'):
                    continue
                if current_item > last_item_harvested_in_last_session:
                    with open('publication_dict.json', 'r') as publication_dict_template:
                        publication_dict = json.load(publication_dict_template)
                    if item.find('mods:title').text in ['Maßstab/Farbkeil', 'Umschlag', 'Titelblatt', 'Inhalt']:
                        continue
                    if ('Heft' in item.find('mods:title').text) or ('Berichtigung' in item.find('mods:title').text):
                        continue
                    publication_dict['title_dict']['main_title'] = item.find('mods:title').text
                    if item.find('mods:subTitle'):
                        publication_dict['title_dict']['sub_title'] = item.find('mods:subTitle').text
                    if 'Beilage' in publication_dict['title_dict']['main_title']:
                        titles_for_supplementing.append(publication_dict['title_dict']['main_title'])
                    if publication_dict['title_dict']['main_title'] in titles_for_supplementing:
                        publication_dict['title_dict']['sub_title'] = 'Deutsches Archaäologisches Institut, Athenische Abteilung, ' + volume_year
                    publication_dict['rdacontent'] = 'txt'
                    publication_dict['rdamedia'] = 'n'
                    publication_dict['rdacarrier'] = 'nc'
                    for author in item.find_all('mods:name'):
                        author_name = ""
                        if author.find_all('mods:roleTerm'):
                            if author_name==author.find('mods:displayForm').text:
                                continue
                            author_name = author.find('mods:displayForm').text
                            publication_dict['authors_list'].append(author_name)
                    publication_dict['field_007'] = 'ta'
                    publication_dict['field_008_18-34'] = 'ar p|| ||||0   b|'
                    if item.find('mods:physicalDescription'):
                        physical_descriptions = item.find('mods:physicalDescription')
                        publication_dict['field_300'] = 'p. ' + physical_descriptions.find('mods:extent', unit='pages').text if physical_descriptions.find('mods:extent', unit='pages') else ''
                    publication_dict['LDR_06_07'] = 'ab'
                    publication_dict['default_language'] = item.find('mods:language').find('mods:languageTerm').text if item.find('mods:language') else 'ger'
                    publication_dict['original_cataloging_agency'] = 'DE-16'
                    publication_dict['retro_digitization_info'] = {'place_of_publisher': '', 'publisher': '', 'date_published_online': ''}
                    publication_dict['fields_590'] = ['arom', '2020xhnxamk']
                    publication_dict['volume'] = volume
                    publication_dict['volume_year'] = volume_year
                    if current_item < 1886:
                        publication_dict['host_item']['name'] = 'Mittheilungen des Deutschen Archäologischen Instituts in Athen'
                    elif current_item < 1915:
                        publication_dict['host_item']['name'] = 'Mitteilungen des Kaiserlich-Deutschen Archäologischen Instituts, Athenische Abteilung'
                    else:
                        publication_dict['host_item']['name'] = 'Mitteilungen des Deutschen Archäologischen Instituts, Athenische Abteilung'
                    publication_dict['host_item']['sysnumber'] = sysnumbers[date_of_publication]
                    publication_dict['publication_year'] = date_of_publication
                    place_of_publication = ''
                    publisher = ''
                    for key in years_published_in:
                        if int(publication_dict['publication_year']) >= key:
                            place_of_publication = publishers[str(key)][0]
                            publisher = publishers[str(key)][1]
                            break
                    publication_dict['publication_etc_statement']['publication'] = {'place': place_of_publication,
                                                                                    'responsible': publisher,
                                                                                    'country_code': 'gw '}
                    publication_dicts.append(publication_dict)
                    items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Mitteilungen des Deutschen Archäologischen Instituts, Athenische Abteilung geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'am', 'Mitteilungen des Deutschen Archäologischen Instituts, Athenische Abteilung', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/am/', 'am', 'Mitteilungen des Deutschen Archäologischen Instituts, Athenische Abteilung', create_publication_dicts)


