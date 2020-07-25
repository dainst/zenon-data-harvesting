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
        volumes_sysnumbers = find_sysnumbers_of_volumes.find_sysnumbers('001597435')
        url = 'http://groma.unibo.it/issue.all'
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
        current_item = int(publication_year + issue.zfill(3))
        if publication_year not in volumes_sysnumbers:
            print('Reviews von Groma konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr', dateTimeObj.strftime("%Y"), 'existiert.')
            print('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr', dateTimeObj.strftime("%Y"), '.')
        else:
            if current_item > last_item_harvested_in_last_session:
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
                                                        if gnd_request_for_cor.check_gnd_for_name(author_tag['content']) else author_tag['content'] for author_tag in article_soup.find_all('meta', attrs={'name': 'DC.Creator.PersonalName'})]
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
                    publication_dict['general_note'] = 'Die Seitenzahlen von Online- und Printausgabe können variieren'
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
                                                if gnd_request_for_cor.check_gnd_for_name(editor) else editor for editor in editorstring.split(',')]
                        elif authorship:
                            authorstring = authorship
                            reviewed_authors = [HumanName(author).last + ', ' + HumanName(author).first
                                                if gnd_request_for_cor.check_gnd_for_name(author) else author for author in authorstring.split(',')]
                        publication_dict['review'] = True
                        publication_dict['review_list'].append({'reviewed_title': reviewed_title,
                                                                'reviewed_authors': reviewed_authors,
                                                                'reviewed_editors': reviewed_editors,
                                                                'year_of_publication': year_of_publication
                                                                })
                    publication_dict["terms_of_use_and_reproduction"] = \
                        {"terms_note": 'All published material is distributed under "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International" (CC BY-NC-ND) license.',
                         "use_and_reproduction_rights": "CC BY-NC-ND", "terms_link": "http://groma.unibo.it/about#nt-3"}
                    publication_dicts.append(publication_dict)
                    items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Groma geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'groma', 'Groma', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/groma/', 'groma', 'Groma', create_publication_dicts)
