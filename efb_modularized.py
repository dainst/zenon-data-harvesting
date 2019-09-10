import urllib.parse
import urllib.request
import create_new_record
from nameparser import HumanName
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")


def harvest():
    with open('records/efb/efb_logfile.json', 'r') as log_file:
        log_dict = json.load(log_file)
        last_item_harvested_in_last_session = log_dict['last_issue_harvested']
        print('Letztes geharvestetes Heft von E-Forschungsberichte:', last_item_harvested_in_last_session)
    issues_harvested = []
    out = open('records/efb/efb_' + timestampStr + '.mrc', 'wb')
    basic_url = 'https://publications.dainst.org/journals/index.php/efb'
    pub_nr = 0
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
    values = {'name': 'Helena Nebel',
              'location': 'Berlin',
              'language': 'Python'}
    headers = {'User-Agent': user_agent}
    data = urllib.parse.urlencode(values)
    data = data.encode('ascii')
    req = urllib.request.Request(basic_url, data, headers)
    with urllib.request.urlopen(req) as response:
        journal_page = response.read()
    journal_page = journal_page.decode('utf-8')
    journal_soup = BeautifulSoup(journal_page, 'html.parser')
    issue_urls = [element.find('a')['href'] for element in journal_soup.find_all('h4')[:-1]]
    for issue_url in issue_urls:
        req = urllib.request.Request(issue_url, data, headers)
        with urllib.request.urlopen(req) as response:
            issue_page = response.read().decode('utf-8')
        issue_soup = BeautifulSoup(issue_page, 'html.parser')
        year = str(max([int(year) for year in re.findall(r'\d{4}', issue_soup.find('h2').text)]))
        issue = str(max([int(issue) for issue in re.findall(r'\d+', issue_soup.find('h3').text)]))
        current_item = int(year+issue.zfill(3))
        if current_item > last_item_harvested_in_last_session:
            for article in issue_soup.find_all('table', class_='tocArticle')[1:]:
                article_url = article.find('div', class_='tocTitle').find('a')['href'].strip()
                req = urllib.request.Request(article_url, data, headers)
                with urllib.request.urlopen(req) as response:
                    article_page = response.read().decode('utf-8')
                article_soup = BeautifulSoup(article_page, 'html.parser')
                with open('publication_dict.json', 'r') as publication_dict_template:
                    publication_dict = json.load(publication_dict_template)
                if article.find('div', class_='tocGalleys').find('a')['href']:
                    publication_dict['pdf_links'].append(article.find('div', class_='tocGalleys').find('a')['href'].strip().replace("view", "download"))
                    publication_dict['authors_list'] = \
                        [HumanName(edit['content']).last + ', ' + HumanName(edit['content']).first for edit in article_soup.find_all('meta', attrs={'name': 'citation_author'})]
                    publication_dict['additional_content'] = {'type': 'Abstract', 'text': article_soup.find('meta', attrs={'name': 'DC.Description'})['content']}
                    publication_dict['rdacontent'] = 'txt'
                    publication_dict['rdamedia'] = 'c'
                    publication_dict['rdacarrier'] = 'cr'
                    publication_dict['host_item']['name'] = 'e-Forschungsberichte des DAI'
                    publication_dict['host_item']['sysnumber'] = '001376930'
                    publication_dict['title_dict']['main_title'] = article_soup.find('meta', attrs={'name': 'citation_title'})['content']
                    publication_dict['publication_year'] = year
                    if article_soup.find('meta', attrs={'name': 'citation_doi'}):
                        publication_dict['doi'] = article_soup.find('meta', attrs={'name': 'citation_doi'})['content']
                    urns = [urn_div.find('a').text for urn_div in article_soup.find('div', class_='panel-body').find_all('div')
                            if create_new_record.link_is_valid(urn_div.find('a')['href']) and 'urn' in urn_div.find('a').text]
                    publication_dict['urn'] = urns[0] if urns else ''
                    publication_dict['LDR_06_07'] = 'ab'
                    publication_dict['field_006'] = 'm     o  d |      '
                    publication_dict['original_cataloging_agency'] = 'DE-2553'
                    publication_dict['publication_etc_statement']['publication'] = {'place': 'Berlin',
                                                                                    'responsible': 'Deutsches Archäologisches Institut',
                                                                                    'country_code': 'gw '}
                    publication_dict['fields_590'] = ['arom', '2019xhnxefb', 'aeforsch', 'daiauf8', 'Online publication']
                    publication_dict['table_of_contents_link'] = issue_url
                    publication_dict['abstract_link'] = article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content'] \
                        if article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'}) else ''
                    publication_dict['field_007'] = 'cr uuu   uu|uu'
                    publication_dict['field_008_18-34'] = 'gr poo||||||   b|'
                    publication_dict['default_language'] = 'de'
                    publication_dict['terms_of_use_and_reproduction']['terms_note'] = article_soup.find('meta', attrs={'name': 'DC.Rights'})['content']
                    publication_dict['host_item']['issn'] = '2198-7734'
                    if create_new_record.check_publication_dict_for_completeness_and_validity(publication_dict):
                        created = create_new_record.create_new_record(out, publication_dict)
                        issues_harvested.append(current_item)
                        pub_nr += created
                    else:
                        break

    print('Es wurden', pub_nr, 'neue Records für e-Forschungsberichte erstellt.')
    if issues_harvested:
        with open('records/efb/efb_logfile.json', 'w') as log_file:
            log_dict = {"last_issue_harvested": max(issues_harvested)}
            json.dump(log_dict, log_file)
            print('Log-File wurde auf', max(issues_harvested), 'geupdated.')


harvest()
