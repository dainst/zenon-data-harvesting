import urllib.parse
import urllib.request
from nameparser import HumanName
from bs4 import BeautifulSoup
import spacy
from langdetect import detect
import language_codes
import re
from datetime import datetime
import json
import write_error_to_logfile
from harvest_records import harvest_records
import gnd_request_for_cor

nlp_dict = {'de': 'de_core_news_sm', 'en': 'en_core_web_sm', 'fr': 'fr_core_news_sm',
            'es': 'es_core_news_sm', 'it': 'it_core_news_sm', 'nl': 'nl_core_news_sm', 'xx': 'xx_ent_wiki_sm'}

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        basic_url = 'https://journals.ub.uni-heidelberg.de/index.php/berrgk/issue/archive/'
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
                volume, volume_year = issue_information.strip().strip("Bd. ").split("(")[0].split(" ")
                publication_year = issue_information.strip().strip("Bd. ").split("(")[1].split(")")[0]
                year = issue_information.strip().strip("Bd. ").split("(")[1].split(")")[0]
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
                        with open('publication_dict.json', 'r') as publication_dict_template:
                            publication_dict = json.load(publication_dict_template)
                        article_url = article.find('div', class_='title').find('a')['href']
                        article_nr += 1
                        req = urllib.request.Request(article_url, data, headers)
                        with urllib.request.urlopen(req) as response:
                            issue_page = response.read().decode('utf-8')
                        article_soup = BeautifulSoup(issue_page, 'html.parser')
                        category = article_soup.find('div', class_="item issue").find_all('div', class_='sub_item')[1].find(
                            'div', class_='value').text.strip()
                        if not any(word in article.text for word in
                                   ["Titelei", "Inhalt", "Vorwort", "Titel", "Literatur", "Beilage",
                                    "Neuerscheinungen", "Besprechungen", "Druckfehler", "Hinweise für Publikationen", "Guidelines for Publications", "Recommandations aux auteurs"]) \
                                and category not in ["Sonstiges", "Literatur", "Editorial"]:
                            publication_dict['text_body_for_lang_detection'] = article_soup.find('meta', attrs={'name': 'DC.Description'})['content']
                            publication_dict['volume'] = volume

                            publication_dict['authors_list'] = [HumanName(author_tag['content']).last + ', ' + HumanName(author_tag['content']).first
                                                                if not gnd_request_for_cor.check_gnd_for_name(author_tag['content']) else author_tag['content']
                                                                for author_tag in article_soup.find_all('meta', attrs={'name': 'citation_author'})]
                            publication_dict['host_item']['name'] = issue_soup.find('title').text.split('): ')[1].split('| ')[0].strip()

                            publication_dict['host_item']['sysnumber'] = '001576648'
                            publication_dict['title_dict']['main_title'] = article_soup.find('meta', attrs={'name': 'citation_title'})['content']
                            publication_dict['publication_year'] = publication_year
                            if article_soup.find('meta', attrs={'name': 'citation_doi'}):
                                publication_dict['doi'] = article_soup.find('meta', attrs={'name': 'citation_doi'})['content']
                            publication_dict['abstract_link'] = article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']
                            if article_soup.find('meta', attrs={'name': 'citation_pdf_url'}):
                                publication_dict['pdf_links'].append(article_soup.find('meta', attrs={'name': 'citation_pdf_url'})['content'])
                            # if article_soup.find('meta', attrs={'name': 'DC.Identifier.pageNumber'}):
                            # publication_dict['pages'] = 'p. ' + article_soup.find('meta', attrs={'name': 'DC.Identifier.pageNumber'})['content']
                            publication_dict['rdacarrier'] = 'cr'
                            publication_dict['rdamedia'] = 'c'
                            publication_dict['rdacontent'] = 'txt'
                            publication_dict['LDR_06_07'] = 'ab'
                            publication_dict['field_006'] = 'm     o  d |      '
                            if int(publication_dict['publication_year']) > 2013:
                                publication_dict['field_007'] = 'cr uuu   uu|uu'
                                publication_dict['default_language'] = language_codes.resolve(article_soup.find('meta', attrs={'name': 'DC.Language'})['content'])
                                publication_dict['do_detect_lang'] = False
                            else:
                                publication_dict['field_007'] = 'cr uuu   uuauu'
                                publication_dict['retro_digitization_info'] = \
                                    {'place_of_publisher': 'Heidelberg', 'publisher': 'Heidelberg UB',
                                     'date_published_online': article_soup.find('div', class_='published').find('div', class_='value').text.strip()}
                                publication_dict['default_language'] = language_codes.resolve(article_soup.find('meta', attrs={'name': 'DC.Language'})['content'])
                            publication_dict['field_008_18-34'] = 'ar poo||||||   b|'
                            publication_dict['fields_590'] = ['arom', '2020xhnxberrgkk', 'Online publication']
                            publication_dict['original_cataloging_agency'] = 'DE-16'
                            publication_dict['publication_etc_statement']['publication'] = {'place': 'Heidelberg',
                                                                                            'responsible': 'Propylaeum',
                                                                                            'country_code': 'gw '}
                            publication_dict['table_of_contents_link'] = issue_url
                            publication_dict['volume_year'] = volume_year
                            publication_dict['copyright_year'] = re.findall(r'\d{4}', article_soup.find('meta', attrs={'name': 'DC.Rights'})['content'])[0]
                            publication_dict['check_for_doublets_and_pars'] = True
                            if article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']:
                                publication_dict['abstract_link'] = article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']
                            if category == "Reviews":
                                rev_authors = ''
                                rev_editors = ''
                                publication_dict['review'] = True
                                for title in publication_dict['title_dict']['main_title'].split(" / "):
                                    for editorship_word in ["Hrsg, von ", "Hrsg. von ", "Herausgegeben von ", "hrsg. von "]:
                                        if editorship_word in title:
                                            rev_editors = title.split(editorship_word)[1]
                                    title = title.strip()
                                    lang = detect(title)
                                    if lang in ["de", "en", "fr", "it", "es", "nl"]:
                                        nlp = spacy.load(nlp_dict['lang'])
                                        tagged_sentence = nlp(title)
                                        propn = False
                                        punct = False
                                        for word in tagged_sentence:
                                            if propn and word.text == "und":
                                                continue
                                            if punct:
                                                break
                                            if word.pos_ not in ["PUNCT", "PROPN"]:
                                                break
                                            if word.pos_ == "PUNCT" and propn and word.text != "-":
                                                punct = True
                                                if len(title.split(word.text)[0].split()) > 1:
                                                    rev_authors = title.split(word.text)[0]
                                            if word.pos_ == "PROPN":
                                                propn = True
                                            else:
                                                propn = False
                                        if not rev_authors:
                                            for ent in tagged_sentence.ents:
                                                if ent.label_ == "PER":
                                                    if title.startswith(ent.text):
                                                        if len(ent.text.split()) > 1:
                                                            rev_authors = ent.text
                                                break
                                    else:
                                        nlp = spacy.load(nlp_dict['xx'])
                                        tagged_sentence = nlp(title)
                                        for ent in tagged_sentence.ents:
                                            if ent.label_ == "PER":
                                                if title.startswith(ent.text):
                                                    if len(ent.text.split()) > 1:
                                                        rev_authors = ent.text
                                                break
                                    if rev_editors:
                                        title = title.split(editorship_word)[0]
                                        title.strip()
                                        rev_editors = [HumanName(edit).last + ', ' + HumanName(edit).first if not gnd_request_for_cor.check_gnd_for_name(edit) else edit
                                                       for edit in rev_editors.split(" und ")]
                                        rev_authors = ''
                                    if rev_authors:
                                        title = title.replace(rev_authors + ", ", "")
                                        rev_authors = [HumanName(auth).last + ', ' + HumanName(auth).first if not gnd_request_for_cor.check_gnd_for_name(auth) else auth
                                                       for auth in rev_authors.split(" und ")]
                                    publication_dict['review_list'].append({'reviewed_title': title,
                                                                            'reviewed_authors': rev_authors,
                                                                            'reviewed_editors': rev_editors,
                                                                            'year_of_publication': '',
                                                                            })
                            publication_dicts.append(publication_dict)
                            items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Berichte der RGK geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'berrgk', 'Berichte der RGK', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/berrgk/', 'berrgk', 'Berichte der RGK', create_publication_dicts)


# Lücke von 1960 bis 2013


'''publishers = {'1908': ['Frankfurt am Main', 'Joseph Baer & Co.'], '1942': ['Berlin', 'de Gruyter'], '1975': ['Mainz', 'von Zabern'],
              '2008': ['Darmstadt', 'von Zabern'], '2015': ['Frankfurt am Main', 'Henrich Editionen']}'''
