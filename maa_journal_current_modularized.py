import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer
import re
from nameparser import HumanName
import json
from datetime import datetime
import write_error_to_logfile
import unidecode
import create_new_record
import find_sysnumbers_of_volumes
from harvest_records import harvest_records


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        dateTimeObj = datetime.now()
        volumes_sysnumbers = find_sysnumbers_of_volumes.find_sysnumbers('000724049')
        titles_processed = []
        basic_url = 'http://www.maajournal.com/'
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
        issues = journal_soup.find_all('div', class_='wifeo_pagesousmenu')
        for issue in issues:
            issue_url = basic_url+issue.find('a')['href']+'#mw999'
            year = re.findall(r'\d{4}', issue.find('a')['href'])[0]
            if dateTimeObj.strftime("%Y") not in volumes_sysnumbers:
                print('Artikel von Mediterranean Archaeology and Archaeometry (MAA) konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr',
                      year, 'existiert.')
                print('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr', year, '.')
                break
            if int(year) < 2019:
                break
            issue_req = urllib.request.Request(issue_url, data, headers)
            with urllib.request.urlopen(issue_req) as issue_response:
                issue_page = issue_response.read()
            issue_soup = BeautifulSoup(issue_page, 'html.parser')
            volume_nr, issue_nr = re.findall(r' (\d{2,3}) - .*? (\d)', issue_soup.find('title').text)[0]
            current_item = int(year + volume_nr.zfill(3) + issue_nr.zfill(2))
            if current_item > last_item_harvested_in_last_session:
                article_info_and_pdf = [item.find('span', class_='style18') for item in issue_soup.find_all('p', class_='style9 style12') if item.find('span', class_='style18') is not None]
                for part in article_info_and_pdf:
                    parts_of_title = [part.strip() for part in part.text.split('\n')]
                    with open('publication_dict.json', 'r') as publication_dict_template:
                        publication_dict = json.load(publication_dict_template)
                    publication_dict['doi'] = ''
                    if "DOI:" in parts_of_title[-1] and create_new_record.doi_is_valid(parts_of_title[-1].replace("DOI:", "").strip()):
                        publication_dict['doi'] = parts_of_title[-1].replace("DOI:", "").strip()
                        del parts_of_title[-1]
                    if len(parts_of_title) == 3:
                        parts_of_title = parts_of_title[:-1]
                    authors = []
                    for entry in parts_of_title:
                        if len(re.findall(r'[a-z]', entry)) >= 3 and not re.findall(r'[A-Z]{4}', entry) and parts_of_title.index(entry) == 1:
                            if len(entry.split(', ')) > len(entry.split()):
                                authors = entry.split(", ")
                                authors = [', '.join([name, authors[authors.index(name)+1]]) for name in authors]
                            else:
                                authors = entry.split(", ")
                            parts_of_title.remove(entry)
                    authors = [re.sub(r'[0-9]', '', aut.strip('\t').strip().strip('\t').strip()) for author in authors for aut in author.split(' and ')]
                    publication_dict['authors_list'] = [author.replace('. ', ', ') if re.findall(r'\w{2}\. ', author) else author if ', ' in author
                                                        else HumanName(author).last + ", " + HumanName(author).first for author in authors]
                    title = unidecode.unidecode(parts_of_title[0])
                    title_word_list = RegexpTokenizer(r'\w+').tokenize(title)
                    title_word_list.sort(key=len, reverse=True)
                    for word in title_word_list:
                        for item in re.findall(r'(?:^|\W)' + word + r'(?:\W|$)', title):
                            if item[0] == "'" and len(item) == 3:
                                title = title.replace(item, item.replace(word, word.lower()))
                            else:
                                title = title.replace(item, item.replace(word, word.capitalize()))
                    if ': ' in title:
                        publication_dict['title_dict']['main_title'], publication_dict['title_dict']['sub_title'] = title.split(': ')
                    else:
                        publication_dict['title_dict']['main_title'], publication_dict['title_dict']['sub_title'] = title, ''
                    publication_dict['table_of_contents_link'] = issue_url
                    publication_dict['default_language'] = 'eng'
                    publication_dict['do_detect_lang'] = True
                    publication_dict['fields_590'] = ['arom', '2020xhnxmaak']
                    publication_dict['original_cataloging_agency'] = 'MAA'
                    publication_dict['publication_year'] = year
                    publication_dict['publication_etc_statement']['publication'] = {'place': 'Rhodes', 'responsible': 'University of the Aegean', 'country_code': 'gr '}
                    publication_dict['rdacontent'] = 'txt'
                    publication_dict['rdamedia'] = 'n'
                    publication_dict['rdacarrier'] = 'nc'
                    publication_dict['host_item']['name'] = 'Mediterranean Archaeology & Archaeometry'
                    publication_dict['host_item']['sysnumber'] = volumes_sysnumbers[year]
                    publication_dict['host_item']['issn'] = '1108-9628'
                    publication_dict['volume'] = volume_nr
                    publication_dict['issue'] = issue_nr
                    publication_dict['LDR_06_07'] = 'ab'
                    publication_dict['field_007'] = 'ta'
                    publication_dict['field_008_18-34'] = ' x p|  |||||   a|'
                    if title not in titles_processed:
                        publication_dicts.append(publication_dict)
                        items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Mediterranean Archaeology & Archaeometry geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'maa', 'Mediterranean Archaeology & Archaeometry', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/maa/', 'maa', 'Mediterranean Archaeology & Archaeometry', create_publication_dicts)
