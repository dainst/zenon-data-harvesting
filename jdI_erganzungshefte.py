import urllib.request, urllib.parse
import json
import urllib.parse, urllib.request
from harvest_records import harvest_records
from bs4 import BeautifulSoup
import write_error_to_logfile


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        basic_url = 'https://digi.ub.uni-heidelberg.de/diglit/jdi_ergh'
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
        volumes_already_processed = []
        for volume_url in volume_urls:
            print(volume_url)
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
            values = {'name': 'Helena Nebel',
                      'location': 'Berlin',
                      'language': 'Python'}
            headers = {'User-Agent': user_agent}
            data = urllib.parse.urlencode(values)
            data = data.encode('ascii')
            req = urllib.request.Request(volume_url, data, headers)
            with urllib.request.urlopen(req) as response:
                volume_page = response.read()
            volume_page = volume_page.decode('utf-8')
            volume_soup = BeautifulSoup(volume_page, 'html.parser')
            date_published_online = volume_soup.find('div', id='publikationsdatum').text.strip().split()[-1]
            volume_year=volume_years[record_nr].split('(')[0].split(', ')[-1]
            mets_url=volume_url.split("?")[0]+'/mets'
            webFile = urllib.request.urlopen(mets_url)
            xml_soup=BeautifulSoup(webFile, 'xml')
            record_nr+=1
            date_of_publication = xml_soup.find_all('mods:mods')[0].find('mods:originInfo').find('mods:dateIssued', keyDate='yes').text
            if '(' in date_of_publication:
                date_of_publication = date_of_publication.split('(')[1].replace(')')
            volume=xml_soup.find_all('mods:mods')[0].find('mods:number').text
            for item in xml_soup.find_all('mods:mods')[:1]:
                current_item = int(volume_year)
                if current_item > last_item_harvested_in_last_session:
                    with open('publication_dict.json', 'r') as publication_dict_template:
                        publication_dict = json.load(publication_dict_template)
                    publication_dict['title_dict']['main_title'] = item.find('mods:title').text.split(' / ')[1]
                    publication_dict['rdacontent'] = 'txt'
                    publication_dict['rdamedia'] = 'c'
                    publication_dict['rdacarrier'] = 'cr'
                    for author in item.find_all('mods:name'):
                        author_name = ""
                        if author.find_all('mods:roleTerm')!=[]:
                            if author_name==author.find('mods:displayForm').text:
                                continue
                            author_name = author.find('mods:displayForm').text
                            publication_dict['authors_list'].append(author_name)
                    publication_dict['field_006'] = 'm     o  d |      '
                    publication_dict['field_007'] = 'cr uuu   uuuuu'
                    if item.find('mods:physicalDescription'):
                        physical_descriptions = item.find('mods:physicalDescription')
                        pages = physical_descriptions.find('mods:extent', unit='pages').text if physical_descriptions.find('mods:extent', unit='pages') else ''
                        ill = physical_descriptions.find('mods:extent', unit='illustrations').text if physical_descriptions.find('mods:extent', unit='illustrations') else ''
                        if ill:
                            publication_dict['additional_fields'].append({'tag': '300', 'indicators': [' ', ' '],
                                              'subfields':
                                                  ['a', '1 online ressource, ' + pages, 'b', ill],
                                              'data': ''})
                        else:
                            publication_dict['field_300'] = '1 online ressource, ' + pages
                            publication_dict['force_300'] = True
                    publication_dict['LDR_06_07'] = 'ab'
                    if item.find('mods:identifier', type='doi'):
                        publication_dict['html_links'].append('https://www.doi.org/' + item.find('mods:identifier', type='doi').text)
                        publication_dict['doi'] = item.find('mods:identifier', type='doi').text
                    else:
                        publication_dict['html_links'].append(item.find('mods:url', access="object in context").text)

                    # sonst überspringen!!!
                    publication_dict['default_language'] = item.find('mods:language').find('mods:languageTerm').text if item.find('mods:language') else 'ger'
                    publication_dict['do_detect_lang'] = False
                    publication_dict['original_cataloging_agency'] = 'DE-16'
                    publication_dict['retro_digitization_info'] = {'place_of_publisher': 'Heidelberg', 'publisher': 'Heidelberg UB', 'date_published_online': date_published_online.strip('.').split('.')[-1]}
                    publication_dict['fields_590'] = ['arom', '2020xhnxjdi', 'Online publication']
                    publication_dict['abstract_link'] =  volume_url
                    publication_dict['host_item']['name'] = 'Jahrbuch des Deutschen Archäologischen Instituts : JdI'
                    publication_dict['host_item']['sysnumber'] = '001578267'
                    publication_dict['volume'] = volume
                    publication_dict['publication_year'] = date_of_publication
                    publication_dict['publication_etc_statement']['publication'] = {'place': 'Berlin; Leipzig',
                                                                                    'responsible': 'Walter de Gruyter & Co.',
                                                                                    'country_code': 'gw '}
                    publication_dict['field_008_18-34'] = ' x p o||||||   b|'
                    publication_dicts.append(publication_dict)
                    items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Jahrbuch des Deutschen Archäologischen Instituts geharvested werden.')
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'jdi', 'Jahrbuch des Deutschen Archäologischen Instituts', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/jdi/', 'jdi', 'Jahrbuch des Deutschen Archäologischen Instituts', create_publication_dicts)
