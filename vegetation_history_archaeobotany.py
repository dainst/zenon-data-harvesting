from nameparser import HumanName
import urllib.parse
import urllib.request
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


dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")

volumes_sysnumbers = {}
volumes_basic_url = 'https://zenon.dainst.org/api/v1/search?lookfor=001579554&type=ParentID&sort=year&page='
# richtige Systemnummer verwenden
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


def harvest(path):
    return_string = ''
    try:
        not_issued = 0
        with open('records/vegetation_history_archaeobotany/vegetation_history_archaeobotany_logfile.json', 'r') as log_file:
            log_dict = json.load(log_file)
            last_issue_harvested_in_last_session = log_dict['last_issue_harvested']
        pub_nr = 0
        page_nr = 1
        issues_harvested = []
        out = open(path + 'vegetation_history_archaeobotany_' + timestampStr + '.mrc', 'wb')
        current_year = int(dateTimeObj.strftime("%Y"))
        url = 'http://api.springernature.com/meta/v2/json?q=issn:0892-7537%20sort:date&s=' + str(page_nr) + '&p=50&api_key=ff7edff14a8f19f744a6fa74860259c8'
        request_nr = 0
        empty_page = False
        while not empty_page:
            request_nr += 1
            url = 'http://api.springernature.com/meta/v2/json?q=issn:0892-7537%20sort:date&s=' + str(page_nr) + '&p=50&api_key=ff7edff14a8f19f744a6fa74860259c8'
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                response = response.read()
            response = response.decode('utf-8')
            json_response = json.loads(response)
            if not json_response['records']:
                empty_page = True
            page_nr += 50
            for article in json_response['records']:
                if 'printDate' in article:
                    publication_year = article['printDate'][:4]
                    issue = str(article['number'])
                    volume = str(article['volume'])
                else:
                    publication_year = article['publicationDate'][:4]
                    issue = str(article['number'])
                    volume = str(article['volume'])

                if publication_year not in volumes_sysnumbers:
                    print('Artikel von Vegetation history and archaeobotany konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr', publication_year, 'existiert.')
                    print('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr', publication_year, '.')
                    continue
                current_item = int(publication_year + volume.zfill(3) + issue[0].zfill(2))
                if current_item > last_issue_harvested_in_last_session:
                    if int(publication_year) > 2000:
                        continue
                    with open('publication_dict.json', 'r') as publication_dict_template:
                        publication_dict = json.load(publication_dict_template)
                    publication_dict['title_dict']['main_title'] = article['title'].split(': ', 1)[0] if len(article['title'].split(": ", 1)) == 2 else article['title']
                    publication_dict['title_dict']['sub_title'] = article['title'].split(': ', 1)[1] if len(article['title'].split(": ", 1)) == 2 else ''
                    publication_dict['authors_list'] = [creator['creator'] for creator in article['creators']]
                    publication_dict['issue'] = issue
                    publication_dict['doi'] = article['doi']
                    publication_dict['LDR_06_07'] = 'ab'
                    publication_dict['do_detect_lang'] = True
                    publication_dict['default_language'] = 'eng'
                    publication_dict['fields_590'] = ['arom', '2020xhnxjowp']
                    publication_dict['original_cataloging_agency'] = 'Springer Nature'
                    publication_dict['publication_year'] = publication_year
                    publication_dict['rdacontent'] = 'txt'
                    publication_dict['rdamedia'] = 'c'
                    publication_dict['rdacarrier'] = 'cr'
                    publication_dict['publication_etc_statement']['publication'] = {'place': 'Heidelberg', 'responsible': 'Springer', 'country_code': 'gw '}
                    publication_dict['host_item'] = {'name': "Journal of World Prehistory", 'sysnumber': volumes_sysnumbers[publication_year], 'issn': '1573-7802'}
                    publication_dict['volume'] = volume
                    publication_dict['field_006'] = 'm     o  d |      '
                    publication_dict['field_007'] = 'cr uuu   uu|uu'
                    publication_dict['field_008_18-34'] = 'qr p o |||||   a|'
                    publication_dict['field_300'] = '1 online resource pp. ' + article['startingPage'] + '-' + article['endingPage']
                    publication_dict['force_300'] = True
                    publication_dict['text_body_for_lang_detection'] = article['abstract']
                    print(int(publication_year), int(dateTimeObj.strftime("%Y")) - 4)
                    if int(publication_year) < 2002:
                        publication_dict['html_links'] = [url['value'] for url in article['url'] if 'html' in url['format'] == 'html']
                        publication_dict['pdf_links'] = [url['value'] for url in article['url'] if url['format'] == 'pdf']
                        print(publication_dict['html_links'], publication_dict['pdf_links'])
                    elif int(publication_year) < (int(dateTimeObj.strftime("%Y")) - 4):
                        publication_dict['html_links'] = ['https://www.jstor.org/openurl?issn=08927537&volume=' + volume + '&issue=' + issue + '&spage=' + article['startingPage']]
                        print(publication_dict['html_links'])
                        publication_dict['general_note'] = "For online access see also parent record"
                    else:
                        publication_dict['force_epub'] = True
                    print(article)
                    if create_new_record.check_publication_dict_for_completeness_and_validity(publication_dict):
                        created = create_new_record.create_new_record(out, publication_dict)
                        issues_harvested.append(current_item)
                        pub_nr += created
                    else:
                        break
        write_error_to_logfile.comment('Letztes geharvestetes Heft von Vegetation history and archaeobotany: ' + str(last_issue_harvested_in_last_session))
        return_string += 'Es wurden ' + str(pub_nr) + ' neue Records für Vegetation history and archaeobotany erstellt.\n'
        if issues_harvested:
            with open('records/vegetation_history_archaeobotany/vegetation_history_archaeobotany_logfile.json', 'w') as log_file:
                log_dict = {"last_issue_harvested": max(issues_harvested)}
                json.dump(log_dict, log_file)
                write_error_to_logfile.comment('Log-File wurde auf ' + str(max(issues_harvested)) + ' geupdated.')
    except Exception as e:
        write_error_to_logfile.write(e)
    return return_string


if __name__ == '__main__':
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%b-%Y")
    harvest('records/vegetation_history_archaeobotany/')
