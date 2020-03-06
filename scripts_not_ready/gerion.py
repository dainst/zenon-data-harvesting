import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import create_new_record
from nameparser import HumanName
from datetime import datetime
import json
import re
import write_error_to_logfile
import os
import find_sysnumbers_of_volumes
from harvest_records import harvest_records


dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")

# volumes_sysnumbers = find_sysnumbers_of_volumes.find_sysnumbers('000058571')


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        url = 'https://dialnet.unirioja.es/revista/619/V/37'
        pub_nr = 0
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
        values = {'name': 'Helena Nebel',
                  'location': 'Berlin',
                  'language': 'Python'}
        headers = {'User-Agent': user_agent}
        data = urllib.parse.urlencode(values)
        data = data.encode('ascii')
        req = urllib.request.Request(url, data, headers)
        with urllib.request.urlopen(req) as response:
            journal_page = response.read()
        journal_page = journal_page.decode('utf-8')
        journal_soup = BeautifulSoup(journal_page, 'html.parser')
        print(journal_soup)
        '''
        volume_urls = ['http://www.libraweb.net/' + link['href'] for link in journal_soup.find_all('a')
                       if (link.text.strip('\n') == 'Online') and ('articoli' in link['href'])]
        for volume_url in volume_urls:
            req = urllib.request.Request(volume_url)
            with urllib.request.urlopen(req) as response:
                volume_page = response.read().decode('utf-8')
            volume_soup = BeautifulSoup(volume_page, 'html.parser')
            url_praefix = volume_url.replace('articoli.php', 'articoli3.php')
            article_urls = [url_praefix + '&articolo=' + article_suffix.find('a')['id'] for article_suffix in volume_soup.find_all('span', class_='asterisco') if article_suffix.find('a')]
            article_urls = [article_url for article_url in article_urls if article_url[-1] != '0']
            for article_url in article_urls:
                req = urllib.request.Request(article_url)
                with urllib.request.urlopen(req) as response:
                    article_page = response.read().decode('utf-8')
                article_info = BeautifulSoup(article_page, 'html.parser')
                article_info = article_info.find('div', class_="twelve columns libra-book-indice")
                if 'DOI' in article_info.text:
                    doi = [url.text for url in [link for link in article_info.find_all('a') if 'href' in link.attrs] if 'dx.medra.org' in url['href']][0]
                else:
                    doi = ''
                title_and_author_info = [info for info in article_info('span', class_='font-xl') if 'Vol.' not in info.text][0]
                volume_info = [info.find('a') for info in article_info('span', class_='font-xl') if 'Vol.' in info.text][0]
                volume_name, volume_year = re.findall(r'([X|V|I|L]+)[^o].+(\d{4})', volume_info.text)[0]
                current_item = int(volume_year)
                if current_item > last_item_harvested_in_last_session:
                    with open('publication_dict.json', 'r') as publication_dict_template:
                        publication_dict = json.load(publication_dict_template)
                    title = title_and_author_info.find('em').text
                    authors = [author.split('/')[0] for author in title_and_author_info.text.replace(title, '').replace('\n', '').split(', ')]
                    pages = re.findall(r'\d{1,3}-\d{1,3}', article_info.text.split('Pagine:')[1].split('Prezzo:')[0])[0]
                    publication_dict['volume'] = volume_name
                    publication_dict['authors_list'] = [HumanName(author).last + ', ' + HumanName(author).first
                                                        for author in authors if author]
                    publication_dict['host_item']['name'] = 'Kókalos'
                    publication_dict['host_item']['sysnumber'] = volumes_sysnumbers[volume_year]
                    publication_dict['title_dict']['main_title'] = title
                    publication_dict['publication_year'] = volume_year
                    publication_dict['doi'] = doi
                    publication_dict['abstract_link'] = article_url
                    publication_dict['html_links'].append(article_url)
                    publication_dict['pages'] = 'p. ' + pages
                    publication_dict['rdacarrier'] = 'cr'
                    publication_dict['rdamedia'] = 'c'
                    publication_dict['rdacontent'] = 'txt'
                    publication_dict['LDR_06_07'] = 'ab'
                    publication_dict['field_006'] = 'm     o  d |      '
                    publication_dict['field_007'] = 'cr uuu   uuuuu'
                    publication_dict['field_008_18-34'] = 'ar p|o||||||   b|'
                    publication_dict['fields_590'] = ['arom', '2020xhnxkokalos', 'Online publication']
                    publication_dict['original_cataloging_agency'] = ''
                    publication_dict['publication_etc_statement']['publication'] = {'place': 'Roma',
                                                                                    'responsible': ' Fabrizio Serra Editore',
                                                                                    'country_code': 'it '}
                    publication_dict['table_of_contents_link'] = volume_url
                    publication_dict['abstract_link'] = article_url
                    publication_dict['field_300'] = '1 online resource (p. ' + pages + ')'
                    publication_dict['force_300'] = True
                    publication_dict['default_language'] = 'ita'
                    publication_dict['do_detect_lang'] = True
                    publication_dicts.append(publication_dict)
                    items_harvested.append(current_item)'''
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Gerion geharvested werden.')
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'gerion', 'Gerion', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/gerion/', 'gerion', 'Gerion', create_publication_dicts)