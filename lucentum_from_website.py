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
import re

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        volumes_sysnumbers = find_sysnumbers('000098920')
        with open('lucentum_38.html', 'r') as html_file:
            volume_soup = BeautifulSoup(html_file.read(), 'html.parser')
        year_of_publication, volume_nr = '2019', '38'
        current_item = int(year_of_publication + volume_nr.zfill(3))
        articles = [item for item in volume_soup.find_all('table', class_='tocArticle') if 'width' not in item.attrs]
        for item in articles:
            with open('publication_dict.json', 'r') as publication_dict_template:
                publication_dict = json.load(publication_dict_template)


            # https://lucentum.ua.es/article/view/2019-n38-produccion-neolitica-sal-marina-la-marismilla-sevilla-datos-renovados-hipotesis-complementarias
            if [pages.text.replace('\n', '').replace('\t', '') for pages in volume_soup.find('div', id='content').find_all('div', class_='tocPages')]:
                pages = [pages.text.replace('\n', '').replace('\t', '') for pages in volume_soup.find('div', id='content').find_all('div', class_='tocPages')][0]
                publication_dict['field_300'] = '1 online resource, pp. ' + pages
            else:
                publication_dict['field_300'] = '1 online resource'
            publication_dict['force_300'] = True
            if year_of_publication not in volumes_sysnumbers:
                write_error_to_logfile.comment('Artikel von Lucentum konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr '
                                               + year_of_publication + ' existiert.')
                write_error_to_logfile.comment('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr ' + year_of_publication + '.')
            publication_dict['title_dict']['main_title'] = item.find('div', class_='tocTitle').find('a').text
            publication_dict['authors_list'] = [HumanName(author).last + ', ' + HumanName(author).first if not gnd_request_for_cor.check_gnd_for_name(author) else author
                                                for author in item.find('div', class_="tocAuthors").text.replace('\n', '').replace('\t', '').split(',')]



            # weiter ab hier!!!

            article_url = item.find('div', class_='tocTitle').find('a')['href']
            req = urllib.request.Request(article_url)
            with urllib.request.urlopen(req) as response:
                article_page = response.read()
            article_page = article_page.decode('utf-8')
            article_soup = BeautifulSoup(article_page, 'html.parser')
            publication_dict['html_links'] = [article_soup.find('a', id="pub-id::doi")['href']]
            publication_dict['doi'] = article_soup.find('a', id="pub-id::doi")['href'].replace('https://doi.org/', '')
            publication_dict['LDR_06_07'] = 'ab'
            publication_dict['do_detect_lang'] = False
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
            publication_dict['volume'] = volume_nr
            publication_dict['field_006'] = 'm     o  d |      '
            publication_dict['field_007'] = 'cr uuu   uu|uu'
            publication_dict['field_008_18-34'] = 'ar p|o |||||   a|'
            publication_dict['terms_of_use_and_reproduction'] = {'terms_note': '', 'use_and_reproduction_rights': 'CC BY-SA 4.0', 'terms_link': 'https://creativecommons.org/licenses/by-sa/4.0/'}
            publication_dict['table_of_contents_link'] = 'https://doi.org/10.14198/LVCENTVM2019.38'
            publication_dict['host_item_is_volume'] = True
            publication_dicts.append(publication_dict)
            items_harvested.append(current_item)
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
