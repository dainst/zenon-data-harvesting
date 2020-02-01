import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import re
import create_new_record
import json
import write_error_to_logfile
from datetime import datetime
from nameparser import HumanName
import language_codes

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")

volumes_sysnumbers = {}
volumes_basic_url = 'https://zenon.dainst.org/api/v1/search?lookfor=001597435&type=ParentID&sort=year&page='
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
        return_string = ''
        with open('records/groma/groma_logfile.json', 'r') as log_file:
            log_dict = json.load(log_file)
            last_issue_harvested_in_last_session = log_dict['last_issue_harvested']
            print('Letztes geharvestetes Issue von Groma:', last_issue_harvested_in_last_session)
        pub_nr = 0
        out = open(path + 'groma_' + timestampStr + '.mrc', 'wb')
        basic_url = 'http://groma.unibo.it/issue.all'
        url = basic_url
        issue_req = urllib.request.Request(url)
        with urllib.request.urlopen(issue_req) as issue_response:
            issue = issue_response.read()
        issue = issue.decode('utf-8')
        issue_soup = BeautifulSoup(issue, 'html.parser')
        issue = re.findall(r' (\d+) ', issue_soup.find('h2', class_='title').text)[0]
        publication_year = issue_soup.find('meta', attrs={'itemprop': 'datePublished'})['content']
        toc_link = issue_soup.find('meta', attrs={'itemprop': 'url'})['content']
        articles = issue_soup.find('section', class_='toc').find_all('article')
        article_urls = ['http://groma.unibo.it/' + article.find('a')['href'] for article in articles]
        current_issue = int(publication_year + issue.zfill(3))
        if publication_year not in volumes_sysnumbers:
            print('Reviews von Groma konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr', dateTimeObj.strftime("%Y"), 'existiert.')
            print('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr', dateTimeObj.strftime("%Y"), '.')
        else:
            if current_issue > last_issue_harvested_in_last_session:
                for article_url in article_urls:
                    article_req = urllib.request.Request(article_url)
                    with urllib.request.urlopen(article_req) as article_response:
                        article = article_response.read()
                    article = article.decode('utf-8')
                    article_soup = BeautifulSoup(article, 'html.parser')
                    # print(article_soup)
                    with open('publication_dict.json', 'r') as publication_dict_template:
                        publication_dict = json.load(publication_dict_template)
                    publication_dict['title_dict']['main_title'] = article_soup.find('meta', attrs={'name': 'DC.Title'})['content']
                    publication_dict['volume'] = issue
                    publication_dict['rdacontent'] = 'txt'
                    publication_dict['rdamedia'] = 'c'
                    publication_dict['rdacarrier'] = 'cr'
                    publication_dict['authors_list'] = [HumanName(author_tag['content']).last + ', ' + HumanName(author_tag['content']).first
                                                        for author_tag in article_soup.find_all('meta', attrs={'name': 'DC.Creator.PersonalName'})]
                    publication_dict['host_item']['name'] = 'Groma : documenting archaeology'
                    publication_dict['host_item']['sysnumber'] = volumes_sysnumbers[publication_year]
                    publication_dict['publication_year'] = publication_year
                    if article_soup.find('meta', attrs={'name': 'DC.Identifier.DOI'}):
                        publication_dict['doi'] = article_soup.find('meta', attrs={'name': 'DC.Identifier.DOI'})['content']
                    publication_dict['LDR_06_07'] = 'ab'
                    publication_dict['field_007'] = 'cr uuu   uu|uu'
                    publication_dict['default_language'] = language_codes.resolve(article_soup.find('meta', attrs={'name': 'DC.Language'})['content'])
                    publication_dict['do_detect_lang'] = True
                    publication_dict['field_008_18-34'] = 'ar p|o||||||   b|'
                    publication_dict['fields_590'] = ['arom', '2020xhnxgroma']
                    publication_dict['original_cataloging_agency'] = 'BraDypUS'
                    publication_dict['publication_etc_statement']['publication'] = {'place': 'Roma',
                                                                                    'responsible': 'BraDypUS',
                                                                                    'country_code': 'it '}
                    publication_dict['table_of_contents_link'] = toc_link
                    publication_dict['field_006'] = 'm     o  d |      '
                    publication_dict['html_links'].append(article_url)
                    # all_tags = [tag.text for tag in article_soup.find('dl', class_='article-metadata').find_all()]
                    # page_tag = [tag for tag in all_tags if 'Pp.' in all_tags[all_tags.index(tag) - 1]]
                    if 'Review of' in publication_dict['title_dict']['main_title'] and '“' in \
                            publication_dict['title_dict']['main_title']:
                        publication_dict['title_dict']['main_title'] = \
                            publication_dict['title_dict']['main_title'].replace("Review of", "").strip(';').strip(':')
                        if re.findall(r'\d{4}', publication_dict['title_dict']['main_title']):
                            year_of_publication = re.findall(r'\d{4}', publication_dict['title_dict']['main_title'])[0]
                        else:
                            year_of_publication = ''
                        authorship, reviewed_title = publication_dict['title_dict']['main_title'].split('“')
                        reviewed_title = reviewed_title.split('”', 1)[0]
                        authorship = authorship.replace(year_of_publication, '').strip()
                        if authorship != '':
                            while any([authorship[-1] == i for i in ['.', ',', ' ']]):
                                    authorship = authorship.strip(authorship[-1])
                        reviewed_editors, reviewed_authors = [], []
                        if any([editorship_word in authorship for editorship_word in ['(ed.)', '(ed)', '(eds.)', '(eds)']]):
                            editorstring = re.sub(r' *\(.+\)', '', authorship)
                            reviewed_editors = [HumanName(editor).last + ', ' + HumanName(editor).first
                                       for editor in editorstring.split(',')]
                        elif authorship:
                            authorstring = authorship
                            reviewed_authors = [HumanName(author).last + ', ' + HumanName(author).first
                                       for author in authorstring.split(',')]
                        publication_dict['review'] = True
                        publication_dict['review_list'].append({'reviewed_title': reviewed_title,
                                                                'reviewed_authors': reviewed_authors,
                                                                'reviewed_editors': reviewed_editors,
                                                                'year_of_publication': year_of_publication
                                                                })
                    publication_dict["terms_of_use_and_reproduction"] = \
                        {"terms_note": 'All published material is distributed under "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International" (CC BY-NC-ND) license.',
                         "use_and_reproduction_rights": "CC BY-NC-ND", "terms_link": "http://groma.unibo.it/about#nt-3"}
                    if create_new_record.check_publication_dict_for_completeness_and_validity(publication_dict):
                        created = create_new_record.create_new_record(out, publication_dict)
                        pub_nr += created
                    else:
                        break
        write_error_to_logfile.comment('Letztes geharvestetes Heft von Groma:' + str(last_issue_harvested_in_last_session))
        return_string += 'Es wurden ' + str(pub_nr) + ' neue Records für Groma erstellt.\n'
        if pub_nr > 0:
            with open('records/groma/groma_logfile.json', 'w') as log_file:
                log_dict = {"last_issue_harvested": current_issue}
                json.dump(log_dict, log_file)
                write_error_to_logfile.comment('Log-File wurde auf ' + str(current_issue) + ' geupdated.')
    except Exception as e:
        write_error_to_logfile.write(e)
    return return_string


if __name__ == '__main__':
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%b-%Y")
    harvest('records/groma/')
