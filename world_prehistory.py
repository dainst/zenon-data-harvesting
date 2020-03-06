import urllib.parse
import urllib.request
import json
import write_error_to_logfile
from datetime import datetime
import find_sysnumbers_of_volumes
from harvest_records import harvest_records


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        volumes_sysnumbers = find_sysnumbers_of_volumes.find_sysnumbers('001579554')
        volumes_sysnumbers['2007'] = volumes_sysnumbers['2006']
        dateTimeObj = datetime.now()
        page_nr = 1
        empty_page = False
        while not empty_page:
            url = 'http://api.springernature.com/meta/v2/json?q=issn:0892-7537%20sort:date&s=' + str(page_nr) + '&p=50&api_key=ff7edff14a8f19f744a6fa74860259c8'
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                response = response.read()
            response = response.decode('utf-8')
            json_response = json.loads(response)
            if not json_response['records']:
                empty_page = True
            page_nr += 50
            for article in json_response['records']:
                if 'coverDate' in article:
                    publication_year = article['coverDate'][:4]
                    issue = str(article['number'])
                    volume = str(article['volume'])
                elif 'printDate' in article:
                    publication_year = article['printDate'][:4]
                    issue = str(article['number'])
                    volume = str(article['volume'])
                else:
                    publication_year = article['publicationDate'][:4]
                    issue = str(article['number'])
                    volume = str(article['volume'])
                current_item = int(publication_year + volume.zfill(3) + issue[0].zfill(2))
                if current_item > last_item_harvested_in_last_session:
                    if int(publication_year) > (int(dateTimeObj.strftime("%Y")) - 4):
                        continue
                    if publication_year not in volumes_sysnumbers:
                        write_error_to_logfile.comment('Artikel von Journal of World Prehistory konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr ' + publication_year + ' existiert.')
                        write_error_to_logfile.comment('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr ' + publication_year + '.')
                        continue
                    with open('publication_dict.json', 'r') as publication_dict_template:
                        publication_dict = json.load(publication_dict_template)
                    publication_dict['title_dict']['main_title'] = article['title'].split(': ', 1)[0] if len(article['title'].split(": ", 1)) == 2 else article['title']
                    publication_dict['title_dict']['sub_title'] = article['title'].split(': ', 1)[1] if len(article['title'].split(": ", 1)) == 2 else ''
                    publication_dict['authors_list'] = [creator['creator'] for creator in article['creators']]
                    publication_dict['issue'] = issue
                    publication_dict['doi'] = article['doi']
                    publication_dict['LDR_06_07'] = 'ab'
                    publication_dict['do_detect_lang'] = True
                    publication_dict['default_language'] = 'eng'
                    publication_dict['fields_590'] = ['arom', '2020xhnxjowp']
                    publication_dict['original_cataloging_agency'] = 'Springer Nature'
                    publication_dict['publication_year'] = publication_year
                    publication_dict['rdacontent'] = 'txt'
                    publication_dict['rdamedia'] = 'c'
                    publication_dict['rdacarrier'] = 'cr'
                    publication_dict['publication_etc_statement']['publication'] = {'place': 'Heidelberg', 'responsible': 'Springer', 'country_code': 'gw '}
                    publication_dict['host_item'] = {'name': "Journal of World Prehistory", 'sysnumber': volumes_sysnumbers[publication_year], 'issn': '1573-7802'}
                    publication_dict['volume'] = volume
                    publication_dict['field_006'] = 'm     o  d |      '
                    publication_dict['field_007'] = 'cr uuu   uu|uu'
                    publication_dict['field_008_18-34'] = 'qr p o |||||   a|'
                    publication_dict['field_300'] = '1 online resource, pp. ' + article['startingPage'] + '-' + article['endingPage']
                    publication_dict['force_300'] = True
                    publication_dict['text_body_for_lang_detection'] = article['abstract']
                    if int(publication_year) < 2003:
                        publication_dict['html_links'] = [url['value'] for url in article['url'] if 'html' in url['format'] == 'html']
                        publication_dict['pdf_links'] = [url['value'] for url in article['url'] if url['format'] == 'pdf']
                    elif int(publication_year) < (int(dateTimeObj.strftime("%Y")) - 3):
                        publication_dict['html_links'] = ['https://www.jstor.org/openurl?issn=08927537&volume=' + volume + '&issue=' + issue + '&spage=' + article['startingPage']]
                        publication_dict['general_note'] = "For online access see also parent record"
                    else:
                        publication_dict['force_epub'] = True
                    publication_dicts.append(publication_dict)
                    items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Journal of World Prehistory geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'world_prehistory', 'Journal of World Prehistory', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/world_prehistory/', 'world_prehistory', 'Journal of World Prehistory', create_publication_dicts)
