import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from nameparser import HumanName
import json
import re
import write_error_to_logfile
from harvest_records import harvest_records

nlp_dict = {'de': 'de_core_news_sm', 'en': 'en_core_web_sm', 'fr': 'fr_core_news_sm',
            'es': 'es_core_news_sm', 'it': 'it_core_news_sm', 'nl': 'nl_core_news_sm', 'xx': 'xx_ent_wiki_sm'}


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        url = 'https://bmcr.brynmawr.edu/publications?page=1'
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            journal_page = response.read()
        journal_page = journal_page.decode('utf-8')
        journal_soup = BeautifulSoup(journal_page, 'html.parser')
        article_links = [tag['href'] for tag in journal_soup.find_all('a', class_='ref-wrapper') if tag.find('p', class_='ref-details')]
        if int(re.findall(r'[\d|.]{10,11}', article_links[-1])[0].replace('.', '')) > last_item_harvested_in_last_session:
            remaining_article_links = []
            item_to_append = last_item_harvested_in_last_session
            last_item_on_page = int(re.findall(r'[\d|.]{10,11}', article_links[-1])[0].replace('.', ''))
            while item_to_append < (last_item_on_page - 1):
                if int(str(item_to_append)[-2:]) < 55:
                    item_to_append += 1
                else:
                    item_to_append += 46
                remaining_article_links.append('http://bmcr.brynmawr.edu/' + str(item_to_append)[:4] + '/' + '.'.join(re.findall(r'^(\d{4})(\d{2})(\d{2})$', str(item_to_append))[0]))
            article_links = remaining_article_links + article_links
        for article_link in article_links:
            current_item = int(re.findall(r'[\d|.]{10,11}', article_link)[0].replace('.', ''))
            if current_item <= last_item_harvested_in_last_session:
                break
            else:
                with open('publication_dict.json', 'r') as publication_dict_template:
                    publication_dict = json.load(publication_dict_template)
                req = urllib.request.Request(article_link)
                try:
                    with urllib.request.urlopen(req) as response:
                        article_page = response.read()
                    article_soup = BeautifulSoup(article_page, 'html.parser')
                    if not article_soup.find('span', itemprop='name'):
                        continue
                    review_author = article_soup.find('span', itemprop='name').text
                    review_tag = [tag.text for tag in article_soup.find_all('h4') if not tag.attrs and 'Review by' in tag.text]
                    response_tag = [tag.text for tag in article_soup.find_all('h4') if not tag.attrs and 'Response by' in tag.text]
                    if review_tag:
                        publication_dict['review'] = True
                    elif response_tag:
                        publication_dict['response'] = True
                    if review_author:
                        publication_dict['authors_list'] = [(HumanName(author).last + ', ' + HumanName(author).first + ' ' + HumanName(author).middle).strip() for and_seperated_authors in
                                                            review_author.split(', ') for author in and_seperated_authors.split(' and ')]
                        publication_year = ''
                    publication_dict['text_body_for_lang_detection'] = article_soup.find_all('div', itemprop='reviewBody')[0].text.strip()
                    if publication_dict['review']:
                        for pub in article_soup.find_all('div', class_='entry-header row'):
                            title_reviewed = pub.find_all('em', itemprop='itemReviewed')[0].text
                            if re.findall(r'.Bd\..', title_reviewed):
                                if len(re.findall(r'.Bd\..*?:', title_reviewed)) == 0:
                                    title_reviewed = title_reviewed.rsplit('Bd.', 1)[0]
                            elif re.findall(r'.\..', title_reviewed):
                                title_reviewed = title_reviewed.rsplit('.', 1)[0]
                            title_reviewed = title_reviewed.strip('.')
                            if re.findall(r'[^\d]\d{4}[^\d]', pub.find('div', class_='entry-citation').text):
                                publication_year = re.findall(r'[^\d](\d{4})[^\d]', pub.find('div', class_='entry-citation').text)[0]
                            else:
                                publication_year = ''
                            reviewed_authors = [string.strip().strip(',') for string in
                                                pub.find('div', class_='entry-citation').text.split(title_reviewed)[0].replace('\t', '').split('\n') if string.strip()]
                            reviewed_authors = [HumanName(reviewed_author).last + ', ' + HumanName(reviewed_author).first for reviewed_author in reviewed_authors]
                            publication_dict['review_list'].append({'reviewed_title': title_reviewed,
                                                                    'reviewed_authors': reviewed_authors,
                                                                    'reviewed_editors': [],
                                                                    'year_of_publication': publication_year,
                                                                    })
                    publication_dict['LDR_06_07'] = 'ab'
                    publication_dict['field_006'] = 'm     o  d |      '
                    publication_dict['field_007'] = 'cr  uuu      uuuuu'
                    publication_dict['field_008_18-34'] = 'k| poooo  ||   b|'
                    publication_dict['original_cataloging_agency'] = 'BMCR'
                    publication_dict['publication_etc_statement']['publication'] = {'place': 'Bryn Mawr, PA',
                                                                                    'responsible': 'Thomas Library, Bryn Mawr College',
                                                                                    'country_code': 'pau'}
                    publication_dict['publication_year'] = re.findall(r'\d{4}', article_link)[0]
                    publication_dict['field_300'] = '1 online resource'
                    publication_dict['rdacontent'] = 'txt'
                    publication_dict['rdamedia'] = 'c'
                    publication_dict['rdacarrier'] = 'cr'
                    publication_dict['fields_590'] = ['arom', 'Online publication', '2020xhnxbmcr']
                    publication_dict['html_links'].append(article_link)
                    publication_dict['host_item'] = {'name': 'Bryn Mawr Classical Review', 'sysnumber': '000810352', 'issn': ''}
                    publication_dict['default_language'] = 'en'
                    publication_dicts.append(publication_dict)
                    items_harvested.append(current_item)
                except Exception as e:
                    write_error_to_logfile.write(e)
                    write_error_to_logfile.comment('URL nicht vorhanden.')
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für BMCR geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'bmcr', 'BMCR', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/bmcr/', 'bmcr', 'BMCR', create_publication_dicts)

# Response funktioniert nicht mehr!