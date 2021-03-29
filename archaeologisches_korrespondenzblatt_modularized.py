import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from nameparser import HumanName
from langdetect import detect
import language_codes
import spacy
import json
import re
import write_error_to_logfile
from harvest_records import harvest_records
import gnd_request_for_cor
import find_sysnumbers_of_volumes
from datetime import datetime

nlp_dict = {'de': 'de_core_news_sm', 'en': 'en_core_web_sm', 'fr': 'fr_core_news_sm',
            'es': 'es_core_news_sm', 'it': 'it_core_news_sm', 'nl': 'nl_core_news_sm', 'xx': 'xx_ent_wiki_sm'}


# https://journals.ub.uni-heidelberg.de/index.php/ak/issue/archive
def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:

        volumes_sysnumbers =  find_sysnumbers_of_volumes.find_sysnumbers('000099473')
        basic_url = 'https://journals.ub.uni-heidelberg.de/index.php/ak/issue/archive/'
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
                issue_information = list_element.find('div', class_='series').text
                volume = issue_information.split("Nr. ")[1].split(" (")[0]
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
                volume_name = issue_soup.find('title').text.split('): ')[1].split('| ')[0].strip()
                for article in [article_tag.find('a') for article_tag in issue_soup.find_all('h2', class_='title') if article_tag.find('a')]:
                    article_url = article['href']
                    req = urllib.request.Request(article_url, data, headers)
                    with urllib.request.urlopen(req) as response:
                        issue_page = response.read().decode('utf-8')
                    article_soup = BeautifulSoup(issue_page, 'html.parser')
                    year = article_soup.find('meta', attrs={'name': 'citation_date'})['content'].split('/')[0]
                    current_item = int(year + str(max([int(vol) for vol in re.findall(r'\d+', volume)])).zfill(3))
                    if current_item > last_item_harvested_in_last_session:
                        category = article_soup.find('div', class_="item issue").find_all('div', class_='sub_item')[1].find(
                            'div', class_='value').text.strip()
                        if not any(word in article.text for word in
                                   ["Titelei", "Inhalt", "Vorwort", "Titel", "Literatur", "Widmung", "Beilage",
                                    "Neuerscheinungen", "Besprechungen"]) and category not in ["Sonstiges", "Literatur", "Editorial"]:
                            with open('publication_dict.json', 'r') as publication_dict_template:
                                publication_dict = json.load(publication_dict_template)
                            publication_dict['authors_list'] = [HumanName(author_tag['content']).last + ', ' + HumanName(author_tag['content']).first
                                                                if not gnd_request_for_cor.check_gnd_for_name(author_tag['content']) else author_tag['content'] for author_tag in article_soup.find_all('meta', attrs={'name': 'citation_author'})]
                            publication_dict['host_item']['name'] = volume_name

                            publication_dict['title_dict']['main_title'] = article_soup.find('meta', attrs={'name': 'citation_title'})['content']
                            publication_dict['publication_year'] = article_soup.find('meta', attrs={'name': 'citation_date'})['content'].split('/')[0]
                            if publication_dict['publication_year'] not in volumes_sysnumbers:
                                write_error_to_logfile.comment('Reviews von Gnomon konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr ' + publication_dict['publication_year'] + ' existiert.')
                                write_error_to_logfile.comment('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr ' + publication_dict['publication_year'] + '.')
                                break
                            publication_dict['host_item']['sysnumber'] = volumes_sysnumbers[publication_dict['publication_year']]
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
                            publication_dict['field_008_18-34'] = 'qr poo||||||   b|'
                            publication_dict['fields_590'] = ['argk', '2021xhnxarkor', 'Online publication']
                            publication_dict['original_cataloging_agency'] = 'DE-16'
                            publication_dict['publication_etc_statement']['publication'] = {'place': 'Heidelberg',
                                                                                            'responsible': 'Propylaeum',
                                                                                            'country_code': 'gw '}
                            publication_dict['table_of_contents_link'] = issue_url
                            publication_dict['abstract_link'] = article_url
                            publication_dict['field_300'] = '1 online resource, ' + publication_dict['pages']
                            publication_dict['force_300'] = True
                            publication_dict['default_language'] = language_codes.resolve(article_soup.find('meta', attrs={'name': 'DC.Language'})['content'])
                            publication_dict['do_detect_lang'] = False
                            publication_dict['check_for_doublets_and_pars'] = True
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
                                        nlp = spacy.load(nlp_dict[lang])
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
                                        rev_editors = [HumanName(edit).last + ', ' + HumanName(edit).first if not gnd_request_for_cor.check_gnd_for_name(edit) else edit for edit in rev_editors.split(" und ")]
                                        rev_authors = ''
                                    if rev_authors:
                                        title = title.replace(rev_authors + ", ", "")
                                        rev_authors = [HumanName(auth).last + ', ' + HumanName(auth).first if not gnd_request_for_cor.check_gnd_for_name(auth) else auth for auth in rev_authors.split(" und ")]
                                    publication_dict['review_list'].append({'reviewed_title': title,
                                                                            'reviewed_authors': rev_authors,
                                                                            'reviewed_editors': rev_editors,
                                                                            'year_of_publication': '',
                                                                            })
                                    publication_dict['review'] = True
                            publication_dicts.append(publication_dict)
                            items_harvested.append(current_item)
    except Exception as e:
            write_error_to_logfile.write(e)
            write_error_to_logfile.comment('Es konnten keine Artikel für Archäologisches Korrespondenzblatt geharvested werden.')
            items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'ak', 'Archäologisches Korrespondenzblatt', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/ak/', 'ak', 'Archäologisches Korrespondenzblatt', create_publication_dicts)
