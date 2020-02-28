import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import create_new_record
from nameparser import HumanName
from langdetect import detect
import language_codes
import spacy
from datetime import datetime
import json
import re
import write_error_to_logfile
import os


dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")


def harvest(path):
    return_string = ''
    pub_nr = 0
    issues_harvested = 0
    try:
        with open('records/hesperia/hesperia.json', 'r') as log_file:
            log_dict = json.load(log_file)
            last_item_harvested_in_last_session = log_dict['last_issue_harvested']
        issues_harvested = []
        out = open(path + 'hesperia' + timestampStr + '.mrc', 'wb')
        url = 'https://www.ascsa.edu.gr/publications/hesperia/volumes'
        pub_nr = 0
        print(url)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            journal_page = response.read()
        journal_page = journal_page.decode('utf-8')
        journal_soup = BeautifulSoup(journal_page, 'html.parser')
        volumes = journal_soup.find_all('div', class_='col text')
        for volume in volumes:
            volume_nr, volume_year = re.findall(r'(\d+)[^\d]+(\d{4})', volume.find('h3').text)[0]
            # print(volume_name)
            issue_urls = ['https://www.ascsa.edu.gr' + issue_link['href'] for issue_link in volume.find_all('a')]
            for issue_url in issue_urls:
                req = urllib.request.Request(issue_url)
                with urllib.request.urlopen(req) as response:
                    issue_page = response.read().decode('utf-8')
                issue_soup = BeautifulSoup(issue_page, 'html.parser')
                article_urls = ['https://www.ascsa.edu.gr' + article_info.find('a')['href']
                       for article_info in issue_soup.find('div', class_="results-list-block").find_all('div', class_='col text')]
                for article_url in article_urls:
                    req = urllib.request.Request(article_url)
                    with urllib.request.urlopen(req) as response:
                        article_page = response.read().decode('utf-8')
                    article_soup = BeautifulSoup(article_page, 'html.parser')
                    article = article_soup.find('div', class_="col-lg-9 main")
                    [s.extract() for s in article('div', id="main-intro-block")]
                    issue_nr = re.findall(r'Issue (\d)', article.text)[0]
                    current_item = int(volume_year + volume_nr.zfill(3) + issue_nr.zfill(2))
                    if current_item > last_item_harvested_in_last_session:
                        with open('publication_dict.json', 'r') as publication_dict_template:
                            publication_dict = json.load(publication_dict_template)
                        publication_dict['volume'] = volume_nr
                        publication_dict['rdacontent'] = 'txt'
                        # publication_dict['rdamedia'] = 'c'
                        # publication_dict['rdacarrier'] = 'cr'
                        '''
                        
                        publication_dict['authors_list'] = [HumanName(author_tag['content']).last + ', ' + HumanName(author_tag['content']).first
                                                            for author_tag in article_soup.find_all('meta', attrs={'name': 'citation_author'})]
                        publication_dict['host_item']['name'] = volume_name
                        publication_dict['host_item']['sysnumber'] = '001527029'
                        publication_dict['title_dict']['main_title'] = article_soup.find('meta', attrs={'name': 'citation_title'})['content']
                        publication_dict['publication_year'] = article_soup.find('meta', attrs={'name': 'citation_date'})['content'].split('/')[0]
                        if article_soup.find('meta', attrs={'name': 'citation_doi'}):
                            publication_dict['doi'] = article_soup.find('meta', attrs={'name': 'citation_doi'})['content']
                        publication_dict['abstract_link'] = article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']
                        if article_soup.find('meta', attrs={'name': 'citation_pdf_url'}):
                            publication_dict['pdf_links'].append(article_soup.find('meta', attrs={'name': 'citation_pdf_url'})['content'])
                        if article_soup.find('meta', attrs={'name': 'DC.Identifier.pageNumber'}):
                            publication_dict['pages'] = 'p. ' + article_soup.find('meta', attrs={'name': 'DC.Identifier.pageNumber'})['content']
                        # publication_dict['retro_digitization_info'] = {'place_of_publisher': 'Heidelberg', 'publisher': 'Heidelberg UB',
                        # 'date_published_online': re.findall(r'\d{4}', article_soup.find('div', class_='published').find('div', class_='value').text.strip())[0]}
                        publication_dict['rdacarrier'] = 'cr'
                        publication_dict['rdamedia'] = 'c'
                        publication_dict['rdacontent'] = 'txt'
                        publication_dict['LDR_06_07'] = 'ab'
                        publication_dict['field_006'] = 'm     o  d |      '
                        publication_dict['field_007'] = 'cr uuu   uuuuu'
                        publication_dict['field_008_18-34'] = 'gr poo||||||   b|'
                        publication_dict['fields_590'] = ['arom', '2020xhnxaegyp', 'Online publication']
                        publication_dict['original_cataloging_agency'] = 'DE-16'
                        publication_dict['publication_etc_statement']['publication'] = {'place': 'Heidelberg',
                                                                                        'responsible': 'Propylaeum',
                                                                                        'country_code': 'gw '}
                        publication_dict['table_of_contents_link'] = issue_url
                        publication_dict['abstract_link'] = article_url
                        publication_dict['field_300'] = '1 online resource'
                        publication_dict['default_language'] = language_codes.resolve(article_soup.find('meta', attrs={'name': 'DC.Language'})['content'])
                        publication_dict['do_detect_lang'] = False
                        if category == "Reviews":
                            publication_dict['review'] = True
                        if create_new_record.check_publication_dict_for_completeness_and_validity(publication_dict):
                            created = create_new_record.create_new_record(out, publication_dict)
                            issues_harvested.append(current_item)
                            pub_nr += created
                        else:
                            break'''
        write_error_to_logfile.comment('Letztes geharvestetes Heft von hesperia: ' + str(last_item_harvested_in_last_session))
    except Exception as e:
        write_error_to_logfile.write(e)
        pub_nr = 0
        if os.path.exists(path + 'hesperia' + timestampStr + '.mrc'):
            os.remove(path + 'hesperia' + timestampStr + '.mrc')
    return_string += 'Es wurden ' + str(pub_nr) + ' neue Records für hesperia erstellt.\n'
    if issues_harvested:
        max(issues_harvested)
        with open('records/hesperia/hesperia.json', 'w') as log_file:
            log_dict = {"last_issue_harvested": max(issues_harvested)}
            json.dump(log_dict, log_file)
            write_error_to_logfile.comment('Log-File wurde auf' + str(max(issues_harvested)) + 'geupdated.')
    return return_string


if __name__ == '__main__':
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%b-%Y")
    harvest('records/hesperia/')