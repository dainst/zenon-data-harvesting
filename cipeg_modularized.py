import urllib.parse
import urllib.request
import language_codes
from bs4 import BeautifulSoup
import create_new_record
import json
from datetime import datetime
import re
from nameparser import HumanName
import write_error_to_logfile

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")


def harvest(path):
    return_string = ''
    try:
        with open('records/cipeg/cipeg_logfile.json', 'r') as log_file:
            log_dict = json.load(log_file)
            last_item_harvested_in_last_session = log_dict['last_issue_harvested']
        pub_nr = 0
        issues_harvested = []
        out = open(path + 'cipeg_' + timestampStr + '.mrc', 'wb')
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
                                                                for author_tag in article_soup.find_all('meta', attrs={'name': 'citation_author'})]
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
                            # bei der Suche nach Textcorpora die pdf-Dateien mit einbeziehen!!!
                            if create_new_record.check_publication_dict_for_completeness_and_validity(publication_dict):
                                created = create_new_record.create_new_record(out, publication_dict)
                                issues_harvested.append(current_item)
                                pub_nr += created
                            else:
                                break
        write_error_to_logfile.comment('Letzte geharvestete Publikation von CIPEG: ' + str(last_item_harvested_in_last_session))
        return_string += 'Es wurden ' + str(pub_nr) + ' neue Records für CIPEG erstellt.\n'
        if issues_harvested:
            with open('records/cipeg/cipeg_logfile.json', 'w') as log_file:
                log_dict = {"last_issue_harvested": max(issues_harvested)}
                json.dump(log_dict, log_file)
                write_error_to_logfile.comment('Log-File wurde auf ' + str(max(issues_harvested)) + ' geupdated.')
    except Exception as e:
        write_error_to_logfile.write(e)
    return return_string

if __name__ == '__main__':
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%b-%Y")
    harvest('records/cipeg/cipeg_' + timestampStr + '.mrc')
