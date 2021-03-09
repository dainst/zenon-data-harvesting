import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import re
import json
import write_error_to_logfile
from datetime import datetime
from nameparser import HumanName
import language_codes
import find_sysnumbers_of_volumes
from harvest_records import harvest_records
import gnd_request_for_cor


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        dateTimeObj = datetime.now()
        basic_url = 'https://elibrary.chbeck.de/zeitschrift/0017-1417'
        volumes_sysnumbers = find_sysnumbers_of_volumes.find_sysnumbers('000046235')
        if dateTimeObj.strftime("%Y") not in volumes_sysnumbers:
            write_error_to_logfile.comment('Reviews von Gnomon konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr ' + dateTimeObj.strftime("%Y") + ' existiert.')
            write_error_to_logfile.comment('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr ' + dateTimeObj.strftime("%Y") + '.')
        else:
            url = basic_url
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
            values = {'name': 'Helena Nebel',
                      'location': 'Berlin',
                      'language': 'Python'}
            headers = {'User-Agent': user_agent}
            data = urllib.parse.urlencode(values)
            data = data.encode('ascii')
            page_req = urllib.request.Request(url, data, headers)
            with urllib.request.urlopen(page_req) as page_response:
                page = page_response.read()
            page = page.decode('utf-8')
            journal_soup = BeautifulSoup(page, 'html.parser')
            volumes = journal_soup.find_all('h4', class_='panel-title')
            list_elements = ['https://elibrary.chbeck.de'+volume.find('a')['href'] for volume in volumes if volume.find('a')is not None]
            for volume_url in list_elements:
                volume_req = urllib.request.Request(volume_url)
                with urllib.request.urlopen(volume_req) as review_response:
                    volume_page = review_response.read()
                volume_soup = BeautifulSoup(volume_page, 'html.parser')
                issue_urls = ['https://elibrary.chbeck.de' + issue_link['href'] for issue_link in volume_soup.find('div', class_='journal').find_all('a')]
                for issue_url in issue_urls:
                    print(issue_url)
                    issue_req = urllib.request.Request(issue_url)
                    with urllib.request.urlopen(issue_req) as issue_response:
                        issue_page = issue_response.read()
                    issue_soup = BeautifulSoup(issue_page, 'html.parser')
                    volume = issue_soup.find('meta', attrs={'name': 'citation_volume'})['content']
                    issue = issue_soup.find('meta', attrs={'name': 'citation_issue'})['content']
                    publication_year = re.findall(r'\d{4}', issue_soup.find('meta', attrs={'name': 'citation_publication_date'})['content'])[0]
                    current_item = int(publication_year + volume.zfill(3) + issue.zfill(3))
                    if current_item <= last_item_harvested_in_last_session:
                        break
                    else:
                        titles_urls = [div.find('a')['href'] for div in issue_soup.find('div', id="toc-panel-body").find_all('div') if div.find('a')]
                        titles_urls = ['https://elibrary.chbeck.de' + title_url for title_url in titles_urls if re.findall(r'-\d+-\d+?/', title_url)]
                        for title_url in titles_urls:
                            print(title_url)
                            if '/vorlagen-und-nachrichten-jahrgang-' in title_url \
                                    or '/bibliographische-beilage' in title_url or 'titelei-jahrgang' in title_url:
                                continue
                            title_req = urllib.request.Request(title_url)
                            with urllib.request.urlopen(title_req) as title_response:
                                title_page = title_response.read()
                            title_soup = BeautifulSoup(title_page, 'html.parser').find('head')
                            with open('publication_dict.json', 'r') as publication_dict_template:
                                publication_dict = json.load(publication_dict_template)
                            if 'VORLAGEN UND NACHRICHTEN' in title_soup.find('title').text:
                                continue
                            publication_dict['title_dict']['main_title'] = title_soup.find('meta', attrs={'name': 'citation_title'})['content']
                            publication_dict['volume'] = title_soup.find('meta', attrs={'name': 'citation_volume'})['content']
                            publication_dict['rdacontent'] = 'txt'
                            publication_dict['rdamedia'] = 'n'
                            publication_dict['rdacarrier'] = 'nc'
                            publication_dict['authors_list'] = [HumanName(author_tag['content']).last + ', ' + HumanName(author_tag['content']).first
                                                                if not gnd_request_for_cor.check_gnd_for_name(author_tag['content']) else author_tag['content']
                                                                for author_tag in title_soup.find_all('meta', attrs={'name': 'citation_author'})]
                            publication_dict['host_item']['name'] = 'Gnomon'
                            publication_dict['host_item']['sysnumber'] = volumes_sysnumbers[publication_year]
                            publication_dict['host_item_is_volume'] = True
                            publication_dict['title_dict']['main_title'] = title_soup.find('meta', attrs={'name': 'citation_title'})['content']
                            publication_dict['publication_year'] = publication_year
                            if title_soup.find('meta', attrs={'name': 'citation_doi'}):
                                publication_dict['doi'] = title_soup.find('meta', attrs={'name': 'citation_doi'})['content']
                            publication_dict['LDR_06_07'] = 'ab'
                            publication_dict['field_007'] = 'ta'
                            publication_dict['default_language'] = language_codes.resolve(title_soup.find('meta', attrs={'name': 'citation_language'})['content'])
                            publication_dict['do_detect_lang'] = False
                            publication_dict['field_008_18-34'] = 'zr p| ||||||   b|'
                            publication_dict['fields_590'] = ['arom', '2021xhnxgnomonk']
                            publication_dict['original_cataloging_agency'] = 'C.H.Beck eLibrary'
                            publication_dict['publication_etc_statement']['publication'] = {'place': 'München',
                                                                                            'responsible': "C. H. Beck'sche Verlagsbuchhandlung",
                                                                                            'country_code': 'gw '}
                            publication_dict['table_of_contents_link'] = issue_url
                            publication_dict['field_300'] = 'Fasc. ' + issue + ', p. ' \
                                                            + title_soup.find('meta', attrs={'name': "citation_firstpage"})['content'] \
                                                            + '-' + title_soup.find('meta', attrs={'name': "citation_lastpage"})['content']
                            publication_dict['review'] = True
                            publication_dict['check_for_doublets_and_pars'] = False
                            reviewed_title = publication_dict['title_dict']['main_title']
                            reviewed_authors = []
                            reviewed_editors = []
                            if len(reviewed_title.split(': ')) > 1:
                                if any(word in reviewed_title.split(': ')[0] for word in [' (Hrsgg.)', ' (Edd.)', ' (Ed.)', ' (Hrsg.)', ' (†)']):
                                    reviewed_editors_string, reviewed_title = reviewed_title.split(': ', 1)
                                    for word in [' (Hrsgg.)', ' (Edd.)', ' (Ed.)', ' (Hrsg.)', ' (†)']:
                                        if word in reviewed_title:
                                            reviewed_editors_string.replace(word, '')
                                            reviewed_editors = reviewed_editors_string.split(', ')
                                elif ((len(reviewed_title.split(': ')[0])/15)/(reviewed_title.split(': ')[0].count(', ') + 1)) < 2:
                                    reviewed_authors_string, reviewed_title = reviewed_title.split(': ', 1)
                                    reviewed_authors = reviewed_authors_string.split(', ')
                            reviewed_authors = [HumanName(reviewed_person).last + ', ' + HumanName(reviewed_person).first
                                                if not gnd_request_for_cor.check_gnd_for_name(reviewed_person) else reviewed_person for reviewed_person in reviewed_authors]
                            reviewed_editors = [HumanName(reviewed_person).last + ', ' + HumanName(reviewed_person).first
                                                if not gnd_request_for_cor.check_gnd_for_name(reviewed_person) else reviewed_person for reviewed_person in reviewed_editors]
                            publication_dict['review_list'].append({'reviewed_title': reviewed_title,
                                                                    'reviewed_authors': reviewed_authors,
                                                                    'reviewed_editors': reviewed_editors,
                                                                    'year_of_publication': ''
                                                                    })
                            publication_dicts.append(publication_dict)
                            items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Gnomon geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'gnomon', 'Gnomon', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/gnomon/', 'gnomon', 'Gnomon', create_publication_dicts)
