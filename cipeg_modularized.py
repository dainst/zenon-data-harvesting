import urllib.parse
import urllib.request
import language_codes
from bs4 import BeautifulSoup
import json
import re
from nameparser import HumanName
import write_error_to_logfile
from harvest_records import harvest_records
import gnd_request_for_cor


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        basic_url = 'https://journals.ub.uni-heidelberg.de/index.php/cipeg/issue/archive/'
        empty_page = False
        page = 0
        while not empty_page:
            page += 1
            url = basic_url + str(page)
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
            list_elements = journal_soup.find_all('div', class_='obj_issue_summary')
            if not list_elements:
                empty_page = True
            for list_element in list_elements:
                issue_information = list_element.find('a', class_='title').text
                volume, year = issue_information.strip().strip("No ").strip(")").split(" (")
                current_item = int(year + str(max([int(vol) for vol in re.findall(r'\d+', volume)])).zfill(3))
                if current_item > last_item_harvested_in_last_session:
                    issue_url = list_element.find('a', class_='title')['href']
                    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
                    values = {'name': 'Helena Nebel',
                              'location': 'Berlin',
                              'language': 'Python'}
                    headers = {'User-Agent': user_agent}
                    data = urllib.parse.urlencode(values)
                    data = data.encode('ascii')
                    req = urllib.request.Request(issue_url, data, headers)
                    with urllib.request.urlopen(req) as response:
                        issue_page = response.read().decode('utf-8')
                    issue_soup = BeautifulSoup(issue_page, 'html.parser')
                    article_nr = 0
                    for article in issue_soup.find_all('div', class_='obj_article_summary'):
                        if not any(word in article.text for word in
                                   ["Front Matter"]):
                            with open('publication_dict.json', 'r') as publication_dict_template:
                                publication_dict = json.load(publication_dict_template)
                            article_url = article.find('div', class_='title').find('a')['href']
                            article_nr += 1
                            article_req = urllib.request.Request(article_url, data, headers)
                            with urllib.request.urlopen(article_req) as response:
                                article_page = response.read().decode('utf-8')
                            article_soup = BeautifulSoup(article_page, 'html.parser')
                            publication_dict['title_dict']['main_title'] = article_soup.find('meta', attrs={'name': 'citation_title'})['content']
                            publication_dict['text_body_for_lang_detection'] = article_soup.find('meta', attrs={'name': 'DC.Description'})['content']
                            publication_dict['volume'] = volume
                            publication_dict['rdacontent'] = 'txt'
                            publication_dict['rdamedia'] = 'c'
                            publication_dict['rdacarrier'] = 'cr'
                            publication_dict['authors_list'] = [HumanName(author_tag['content']).last + ', ' + HumanName(author_tag['content']).first
                                                                if not gnd_request_for_cor.check_gnd_for_name(author_tag['content']) else author_tag['content'] for author_tag in article_soup.find_all('meta', attrs={'name': 'citation_author'})]
                            publication_dict['host_item']['name'] = 'CIPEG journal : Ancient Egyptian & Sudanese collections and museums'
                            publication_dict['host_item']['sysnumber'] = '001577954'
                            publication_dict['title_dict']['main_title'] = article_soup.find('meta', attrs={'name': 'citation_title'})['content']
                            publication_dict['publication_year'] = year
                            if article_soup.find('meta', attrs={'name': 'citation_doi'}):
                                publication_dict['doi'] = article_soup.find('meta', attrs={'name': 'citation_doi'})['content']
                            publication_dict['abstract_link'] = article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']
                            if article_soup.find('meta', attrs={'name': 'citation_pdf_url'}):
                                publication_dict['pdf_links'].append(article_soup.find('meta', attrs={'name': 'citation_pdf_url'})['content'])
                            publication_dict['rdacarrier'] = 'cr'
                            publication_dict['rdamedia'] = 'c'
                            publication_dict['rdacontent'] = 'txt'
                            publication_dict['LDR_06_07'] = 'ab'
                            publication_dict['field_006'] = 'm     o  d |      '
                            publication_dict['field_007'] = 'cr uuu   uu|uu'
                            publication_dict['default_language'] = language_codes.resolve(article_soup.find('meta', attrs={'name': 'DC.Language'})['content'])
                            publication_dict['do_detect_lang'] = False
                            publication_dict['field_008_18-34'] = 'ar poo||||||   b|'
                            publication_dict['fields_590'] = ['arom', '2020xhnxcipeg', 'Online publication']
                            publication_dict['original_cataloging_agency'] = 'DE-16'
                            publication_dict['publication_etc_statement']['publication'] = {'place': 'Heidelberg',
                                                                                            'responsible': 'Propylaeum',
                                                                                            'country_code': 'gw '}
                            publication_dict['table_of_contents_link'] = issue_url
                            publication_dict['volume_year'] = year
                            publication_dict['copyright_year'] = re.findall(r'\d{4}', article_soup.find('meta', attrs={'name': 'DC.Rights'})['content'])[0]
                            if article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']:
                                publication_dict['abstract_link'] = article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']
                            publication_dicts.append(publication_dict)
                            items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Cipeg geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'cipeg', 'Cipeg', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/cipeg/', 'cipeg', 'Cipeg', create_publication_dicts)
