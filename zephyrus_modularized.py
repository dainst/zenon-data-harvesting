import urllib.parse
import urllib.request
import json
import write_error_to_logfile
from datetime import datetime
from find_sysnumbers_of_volumes import find_sysnumbers
from harvest_records import harvest_records
from nameparser import HumanName

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        volumes_sysnumbers = find_sysnumbers('000035083')
        current_year = int(dateTimeObj.strftime("%Y"))
        year = current_year
        while year > (current_year - 2):
            basic_url = 'https://doaj.org/api/v1/search/articles/bibjson.year:' + str(year) + '%20eissn:0514-7336?page=1&pageSize=100'
            year -= 1
            req = urllib.request.Request(basic_url)
            with urllib.request.urlopen(req) as response:
                response = response.read()
            response = response.decode('utf-8')
            json_response = json.loads(response)
            for item in json_response['results']:
                year_of_publication = str(item['bibjson']['year'])
                volume = item['bibjson']['journal']['volume']
                issue = item['bibjson']['journal']['number'] if item['bibjson']['journal']['number'] else ''
                if year_of_publication not in volumes_sysnumbers:
                    write_error_to_logfile.comment('Artikel von Zephyrus konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr '
                                                   + year_of_publication + ' existiert.')
                    write_error_to_logfile.comment('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr ' + year_of_publication + '.')
                    break
                current_item = int(year_of_publication + volume.zfill(3) + issue.zfill(2))
                if current_item > last_item_harvested_in_last_session:
                    if item['bibjson']['title'] not in ['Zephyrus', 'Créditos', 'Índice', 'Index', 'Índice analítico']:
                        with open('publication_dict.json', 'r') as publication_dict_template:
                            publication_dict = json.load(publication_dict_template)
                        publication_dict['title_dict']['main_title'] = item['bibjson']['title']
                        publication_dict['authors_list'] = [HumanName(author['name']).last.capitalize() + ', ' + HumanName(author['name']).first for author in item['bibjson']['author']]
                        publication_dict['html_links'] = ([link['url'] for link in item['bibjson']['link'] if link['content_type'] == 'html'])
                        publication_dict['issue'] = issue
                        if [identifier['id'] for identifier in item['bibjson']['identifier'] if identifier == 'doi']:
                            publication_dict['doi'] = [identifier['id'] for identifier in item['bibjson']['identifier'] if identifier == 'doi'][0]
                        publication_dict['LDR_06_07'] = 'ab'
                        publication_dict['do_detect_lang'] = True
                        publication_dict['default_language'] = 'spa'
                        publication_dict['fields_590'] = ['arom', '2020xhnxzeph']
                        publication_dict['original_cataloging_agency'] = 'DOAJ'
                        publication_dict['publication_year'] = year_of_publication
                        publication_dict['publication_etc_statement']['publication'] = {'place': 'Salamanca', 'responsible': 'Ediciones Universidad de Salamanca', 'country_code': 'sp '}
                        publication_dict['rdacontent'] = 'txt'
                        publication_dict['rdamedia'] = 'c'
                        publication_dict['rdacarrier'] = 'cr'
                        publication_dict['host_item'] = {'name': " Zephyrus: revista de prehistoria y arqueología", 'sysnumber': volumes_sysnumbers[year_of_publication]}
                        publication_dict['host_item']['issn'] = '2386-3943'
                        publication_dict['volume'] = volume
                        publication_dict['field_006'] = 'm     o  d |      '
                        publication_dict['field_007'] = 'cr uuu   uu|uu'
                        publication_dict['field_008_18-34'] = 'gr p|o |||||   a|'
                        publication_dict['field_300'] = '1 online resource, pp. ' + item['bibjson']['start_page'] + '-' + item['bibjson']['end_page']
                        publication_dict['force_300'] = True
                        if 'abstract' in item['bibjson']:
                            print('abstract', publication_dict['html_links'])
                        else:
                            print('no abstract', publication_dict['html_links'])
                        publication_dict['terms_of_use_and_reproduction'] = {'terms_note': '', 'use_and_reproduction_rights': 'CC BY-SA 4.0', 'terms_link': 'https://creativecommons.org/licenses/by-sa/4.0/'}
                        publication_dicts.append(publication_dict)
                        items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Zephyrus geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'zepyhrus', 'Zephyrus', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/zephyrus/', 'zephyrus', 'Zephyrus', create_publication_dicts)
