import urllib.parse
import urllib.request
import json
import write_error_to_logfile
from datetime import datetime
from find_sysnumbers_of_volumes import find_sysnumbers
from harvest_records import harvest_records
from nameparser import HumanName
import gnd_request_for_cor
from bs4 import BeautifulSoup

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        volumes_sysnumbers = find_sysnumbers('000098920')
        current_year = int(dateTimeObj.strftime("%Y"))
        year = 2020
        while year > (current_year - 2):
            basic_url = 'https://doaj.org/api/v1/search/articles/bibjson.year:' + str(year) + '%20eissn:1989-9904?page=1&pageSize=100'
            print(basic_url)
            year -= 1
            req = urllib.request.Request(basic_url)
            with urllib.request.urlopen(req) as response:
                response = response.read()
            response = response.decode('utf-8')
            json_response = json.loads(response)
            item_nr = 0
            for item in json_response['results']:
                year_of_publication = str(item['bibjson']['year'])
                volume = item['bibjson']['journal']['number']
                issue = ''
                if year_of_publication not in volumes_sysnumbers:
                    write_error_to_logfile.comment('Artikel von Lucentum konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr '
                                                   + year_of_publication + ' existiert.')
                    write_error_to_logfile.comment('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr ' + year_of_publication + '.')
                    break
                current_item = int(year_of_publication + volume.zfill(3) + issue.zfill(2))
                print(current_item)
                if current_item > last_item_harvested_in_last_session:
                    if item['bibjson']['title'] not in ['Lucentum', 'Créditos', 'Índice', 'Index', 'Índice analítico']:
                        with open('publication_dict.json', 'r') as publication_dict_template:
                            publication_dict = json.load(publication_dict_template)
                        publication_dict['title_dict']['main_title'] = item['bibjson']['title']
                        publication_dict['authors_list'] = [author['name'] if not gnd_request_for_cor.check_gnd_for_name(author['name']) else author for author in item['bibjson']['author']]

                        publication_dict['html_links'] = ([link['url'] for link in item['bibjson']['link'] if link['type'] == 'fulltext'])
                        publication_dict['issue'] = issue
                        if [identifier['id'] for identifier in item['bibjson']['identifier'] if identifier['type'] == 'doi']:
                            publication_dict['doi'] = [identifier['id'] for identifier in item['bibjson']['identifier'] if identifier['type'] == 'doi'][0]
                            publication_dict['html_links'] = ['https://doi.org/' + publication_dict['doi']]
                        publication_dict['LDR_06_07'] = 'ab'
                        publication_dict['do_detect_lang'] = True
                        publication_dict['default_language'] = 'spa'
                        publication_dict['fields_590'] = ['arom', '2020xhnxluck']
                        publication_dict['original_cataloging_agency'] = 'DOAJ'
                        publication_dict['publication_year'] = year_of_publication
                        publication_dict['publication_etc_statement']['publication'] = {'place':  'Alicante', 'responsible': 'Servicio de Publicaciones de la Universidad', 'country_code': 'sp '}
                        publication_dict['rdacontent'] = 'txt'
                        publication_dict['rdamedia'] = 'c'
                        publication_dict['rdacarrier'] = 'cr'
                        publication_dict['host_item'] = {'name': "Lucentum : anales de la Universidad de Alicante", 'sysnumber': volumes_sysnumbers[year_of_publication]}
                        publication_dict['host_item']['issn'] = '1989-9904'
                        publication_dict['host_item_is_volume'] = True
                        publication_dict['volume'] = volume
                        publication_dict['field_006'] = 'm     o  d |      '
                        publication_dict['field_007'] = 'cr uuu   uu|uu'
                        publication_dict['field_008_18-34'] = 'ar p|o |||||   a|'
                        basic_url = 'https://doi.org/' + publication_dict['doi'][:-3]
                        publication_dict['table_of_contents_link'] = basic_url
                        year -= 1
                        req = urllib.request.Request(basic_url)
                        with urllib.request.urlopen(req) as response:
                            response = response.read()
                        response = response.decode('utf-8')
                        volume_soup = BeautifulSoup(response, 'html.parser')
                        print(basic_url)
                        if [pages.text.replace('\n', '').replace('\t', '') for pages in volume_soup.find('div', id='content').find_all('div', class_='tocPages') if pages.text.replace('\n', '').replace('\t', '').find(item['bibjson']['start_page']) == 0]:
                            pages = [pages.text.replace('\n', '').replace('\t', '') for pages in volume_soup.find('div', id='content').find_all('div', class_='tocPages') if pages.text.replace('\n', '').replace('\t', '').split('-')[0] == item['bibjson']['start_page']][0]
                            publication_dict['field_300'] = '1 online resource, pp. ' + pages
                        else:
                            publication_dict['field_300'] = '1 online resource'
                        publication_dict['force_300'] = True
                        if 'abstract' not in item['bibjson']:
                            publication_dict['review'] = True
                            publication_dict['review_list'].append({"reviewed_title": publication_dict['title_dict']['main_title'], "reviewed_authors": [],
                                                                "reviewed_editors": [], "year_of_publication": ""})
                        publication_dict['terms_of_use_and_reproduction'] = {'terms_note': '', 'use_and_reproduction_rights': 'CC BY-SA 4.0', 'terms_link': 'https://creativecommons.org/licenses/by-sa/4.0/'}
                        publication_dicts.append(publication_dict)
                        items_harvested.append(current_item)
                        item_nr += 1
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Lucentum geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'lucentum', 'Lucentum', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/lucentum/', 'lucentum', 'Lucentum', create_publication_dicts)
