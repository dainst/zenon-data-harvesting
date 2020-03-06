from nameparser import HumanName
import urllib.parse
import urllib.request
import json
import write_error_to_logfile
from datetime import datetime
from bs4 import BeautifulSoup
import language_codes
import find_sysnumbers_of_volumes
from harvest_records import harvest_records


def create_review_dict(review_title):
    review_title = review_title.replace(" (review)", "")
    review_list = []
    for title in review_title.split(" and: "):
        new_review = {'year_of_publication': ''}
        title = title.strip(",")
        if " ed. by " in title:
            new_review['reviewed_title'], new_review['reviewed_editors'] = title.split(" ed. by ")
            new_review['reviewed_authors'] = []
        elif " eds. by " in title:
            new_review['reviewed_title'], new_review['reviewed_editors'] = title.split(" eds. by ")
            new_review['reviewed_authors'] = []
        elif "trans. by" in title:
            new_review['reviewed_title'], new_review['reviewed_editors'] = title.split(" trans. by ")
            new_review['reviewed_authors'] = []
        elif " by " in title:
            new_review['reviewed_title'], new_review['reviewed_authors'] = title.split(" by ")
            new_review['reviewed_editors'] = []
        for responsibles in ['reviewed_editors', 'reviewed_authors']:
            if new_review[responsibles]:
                new_review[responsibles] = [(HumanName(person).last+", "+HumanName(person).first).strip() for person in new_review[responsibles].split(', ')[0].split(' and ')]
        review_list.append(new_review)
    return review_list


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        volumes_sysnumbers = find_sysnumbers_of_volumes.find_sysnumbers('000793833')
        dateTimeObj = datetime.now()
        current_year = int(dateTimeObj.strftime("%Y"))
        basic_url = 'https://api.crossref.org/journals/1942-1273/works?filter=from-print-pub-date%3A' \
                    + str(current_year - 1) + ',type%3Ajournal-article&cursor='
        next_cursor = '*'
        request_nr = 0
        while True:
            request_nr += 1
            req = urllib.request.Request(basic_url + next_cursor)
            with urllib.request.urlopen(req) as response:
                response = response.read()
            response = response.decode('utf-8')
            json_response = json.loads(response)
            next_cursor = json_response['message']['next-cursor'].replace('+', '%2B')
            if not json_response['message']['items']:
                break
            for item in json_response['message']['items']:
                volume, issue, year_of_publication = item['volume'], item['journal-issue']['issue'], str(item['issued']['date-parts'][0][0])
                if year_of_publication not in volumes_sysnumbers:
                    write_error_to_logfile.comment('Artikel von Journal of Late Antiquity konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr '
                                                   + year_of_publication + ' existiert.')
                    write_error_to_logfile.comment('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr ' + year_of_publication + '.')
                    break
                current_item = int(year_of_publication + volume.zfill(2) + issue.zfill(2))
                if current_item > last_item_harvested_in_last_session:
                    if item['title'][0] not in ["Volume Table of Contents", "Volume Contents", "From the Editor", "Bibliography", "From the Guest Editors"]:
                        with open('publication_dict.json', 'r') as publication_dict_template:
                            publication_dict = json.load(publication_dict_template)
                        publication_dict['authors_list'] = [author['family'] + ', ' + author['given'] for author in item['author']]
                        publication_dict['abstract_link'] = item['URL']
                        publication_dict['pages'] = item['page']
                        publication_dict['issue'] = issue
                        publication_dict['doi'] = item['DOI']
                        if "(review)" in item['title'][0]:
                            publication_dict['review'] = True
                            publication_dict['review_list'] += create_review_dict(item['title'][0])
                        elif any(word in item['title'][0] for word in [" eds. by ", " ed. by ", " by "]):
                            article_url = 'https://www.doi.org/' + publication_dict['doi']
                            req = urllib.request.Request(article_url)
                            with urllib.request.urlopen(req) as response:
                                article_page = response.read().decode('utf-8')
                            article_title = BeautifulSoup(article_page, 'html.parser').find('title').text
                            if "(review)" in article_title:
                                publication_dict['review'] = True
                                publication_dict['review_list'] += create_review_dict(item['title'][0])
                        else:
                            publication_dict['title_dict']['main_title'] = item['title'][0].split(': ', 1)[0] if len(item['title'][0].split(": ", 1)) == 2 else item['title'][0]
                            publication_dict['title_dict']['sub_title'] = item['title'][0].split(': ', 1)[1] if len(item['title'][0].split(": ", 1)) == 2 else ''
                        publication_dict['LDR_06_07'] = 'ab'
                        publication_dict['do_detect_lang'] = False
                        publication_dict['default_language'] = language_codes.resolve(item['language'])
                        publication_dict['fields_590'] = ['arom', '2020xhnxjola']
                        publication_dict['original_cataloging_agency'] = 'Crossref'
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
                        publication_dicts.append(publication_dict)
                        items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Journal of Late Antiquity geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'late_antiquity', 'Journal of Late Antiquity', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/late_antiquity/', 'late_antiquity', 'Journal of Late Antiquity', create_publication_dicts)
