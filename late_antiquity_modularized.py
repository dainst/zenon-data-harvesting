from nameparser import HumanName
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import re
import create_new_record
import json
import write_error_to_logfile
from datetime import datetime


def create_review_dict(review_title):
    review_title = review_title.replace(" (review)", "")
    review_list = []
    for title in review_title.split(" and: "):
        new_review = {'year_of_publication': ''}
        title = title.strip(",")
        if " ed. by " in title:
            new_review['reviewed_title'], new_review['reviewed_editors'] = title.split(" ed. by ")
            new_review['reviewed_authors'] = ''
        elif " eds. by " in title:
            new_review['reviewed_title'], new_review['reviewed_editors'] = title.split(" eds. by ")
            new_review['reviewed_authors'] = ''
        elif " by " in title:
            new_review['reviewed_title'], new_review['reviewed_authors'] = title.split(" by ")
            new_review['reviewed_editors'] = ''
        else:
            new_review['reviewed_title'], new_review['reviewed_authors'], new_review['reviewed_editors'] = title, [], []
        for responsibles in ['reviewed_editors', 'reviewed_authors']:
            if new_review[responsibles]:
                new_review[responsibles] = [(HumanName(person).last+", "+HumanName(person).first).strip() for person in new_review[responsibles].split(', ')[0].split(' and ')]
        review_list.append(new_review)
    return review_list


dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")

volumes_sysnumbers = {}
volumes_basic_url = 'https://zenon.dainst.org/api/v1/search?lookfor=000793833&type=ParentID&sort=year&page='
page_nr = 0
empty_page = False
while not empty_page:
    page_nr += 1
    volume_record_url = volumes_basic_url + str(page_nr)
    req = urllib.request.Request(volume_record_url)
    with urllib.request.urlopen(req) as response:
        response = response.read()
    response = response.decode('utf-8')
    json_response = json.loads(response)
    if 'records' not in json_response:
        empty_page = True
        continue
    for result in json_response['records']:
        for date in result['publicationDates']:
            volumes_sysnumbers[date] = result['id']


def harvest():
    return_string = ''
    try:
        with open('records/late_antiquity/late_antiquity_logfile.json', 'r') as log_file:
            log_dict = json.load(log_file)
            last_issue_harvested_in_last_session = log_dict['last_issue_harvested']
        pub_nr = 0
        issues_harvested = []
        out = open('records/late_antiquity/late_antiquity_' + timestampStr + '.mrc', 'wb')
        basic_url = 'https://muse.jhu.edu/journal/399'
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
        urls = ['https://muse.jhu.edu' + list_element.find('a')['href'] for list_element in journal_soup.find_all('li', class_='volume') if list_element.find('a')]
        volume_names = [list_element.find('a').text for list_element in journal_soup.find_all('li', class_='volume') if list_element.find('a')]
        for issue_url in urls:
            volume_name = volume_names[urls.index(issue_url)]
            volume, issue, year_of_publication = re.findall(r'Volume (\d{1,2}), Number (\d), \w+ (\d{4})', volume_name)[0]
            if year_of_publication not in volumes_sysnumbers:
                print('Artikel von Journal of Late Antiquity konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr', year_of_publication, 'existiert.')
                print('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr', year_of_publication, '.')
                break
            current_item = int(year_of_publication + volume.zfill(2) + issue.zfill(2))
            if current_item > last_issue_harvested_in_last_session:
                req = urllib.request.Request(issue_url, data, headers)
                with urllib.request.urlopen(req) as response:
                    issue_page = response.read().decode('utf-8')
                issue_soup = BeautifulSoup(issue_page, 'html.parser')
                articles = issue_soup.find_all('div', class_='card_text')[1:-1]
                for article in articles:
                    if article.ol.a.text not in ["Volume Table of Contents", "Volume Contents", "From the Editor", "Bibliography", "From the Guest Editors"]:
                        with open('publication_dict.json', 'r') as publication_dict_template:
                            publication_dict = json.load(publication_dict_template)
                        article_url = 'https://muse.jhu.edu' + article.ol.find('li', class_='title').a['href']
                        req = urllib.request.Request(article_url, data, headers)
                        with urllib.request.urlopen(req) as response:
                            article_page = response.read().decode('utf-8')
                        article_soup = BeautifulSoup(article_page, 'html.parser')
                        if '(review)' in article.ol.a.text:
                            publication_dict['review'] = True
                            publication_dict['review_list'] = create_review_dict(article.ol.a.text)
                        else:
                            publication_dict['title_dict']['main_title'] = article.ol.a.text.split(': ', 1)[0] if len(article.ol.a.text.split(": ", 1)) == 2 else article.ol.a.text
                            publication_dict['title_dict']['sub_title'] = article.ol.a.text.split(': ', 1)[1] if len(article.ol.a.text.split(": ", 1)) == 2 else ''
                        publication_dict['authors_list'] = [HumanName(author.text).last + ', ' + HumanName(author.text).first for author in article.ol.find('li', class_='author').find_all('a')]
                        publication_dict['abstract_link'] = article_url
                        publication_dict['pages'] = article_soup.find('li', class_='pg').text
                        publication_dict['issue'] = issue
                        if article_soup.find('li', class_='doi'):
                            publication_dict['doi'] = article_soup.find('li', class_='doi').a.text
                        publication_dict['LDR_06_07'] = 'ab'
                        if not publication_dict['review']:
                            publication_dict['text_body_for_lang_detection'] = article_soup.find('div', class_='abstract').find('p').text
                            publication_dict['abstract_link'] = article_url
                        publication_dict['table_of_contents_link'] = issue_url
                        publication_dict['default_language'] = 'eng'
                        publication_dict['do_detect_lang'] = True
                        publication_dict['fields_590'] = ['arom', '2019xhnxjola']
                        publication_dict['original_cataloging_agency'] = 'Journal of Late Antiquity'
                        publication_dict['publication_year'] = year_of_publication
                        publication_dict['publication_etc_statement']['publication'] = {'place': 'Baltimore, MD', 'responsible': 'Johns Hopkins University Press', 'country_code': 'mdu'}
                        publication_dict['rdacontent'] = 'txt'
                        publication_dict['rdamedia'] = 'n'
                        publication_dict['rdacarrier'] = 'nc'
                        publication_dict['host_item'] = {'name': 'Journal of Late Antiquity', 'sysnumber': volumes_sysnumbers[year_of_publication]}
                        publication_dict['host_item']['issn'] = '1939-6716'
                        publication_dict['volume'] = volume
                        publication_dict['field_007'] = 'ta'
                        publication_dict['field_008_18-34'] = 'fr p|  |||||   a|'
                        if create_new_record.check_publication_dict_for_completeness_and_validity(publication_dict):
                            created = create_new_record.create_new_record(out, publication_dict)
                            issues_harvested.append(current_item)
                            pub_nr += created
                        else:
                            break
        write_error_to_logfile.comment('Letztes geharvestetes Heft von Late Antiquity: ' + str(last_issue_harvested_in_last_session))
        return_string += 'Es wurden ' + str(pub_nr) + ' neue Records für Journal of Late Antiquity erstellt.'
        if issues_harvested:
            with open('records/late_antiquity/late_antiquity_logfile.json', 'w') as log_file:
                log_dict = {"last_issue_harvested": max(issues_harvested)}
                json.dump(log_dict, log_file)
                write_error_to_logfile.comment('Log-File wurde auf ' + str(max(issues_harvested)) + ' geupdated.')
    except Exception as e:
        write_error_to_logfile.write(e)
