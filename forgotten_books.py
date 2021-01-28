import urllib.parse, urllib.request
import urllib.parse, urllib.request
from bs4 import BeautifulSoup
import json
import write_error_to_logfile
from harvest_records import harvest_records
import os
import gzip
from pymarc import MARCReader


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        start_harvesting = False
        nr = 0
        previously_harvested = []
        '''for filestring in os.listdir('fobo'):
            with open('fobo/' + filestring, 'rb') as file:
                new_reader = MARCReader(file)
                for record in new_reader:
                    previously_harvested.append(record['856']['u'])
                    print('previously harvested:', record['856']['u'])'''
        for publication_file in os.listdir('gai_metadata'):
            if nr == 1800:
                break
            try:
                with open('publication_dict.json', 'r') as publication_dict_template:
                    publication_dict = json.load(publication_dict_template)
                publication_xml = open('gai_metadata/' + publication_file, 'r')
                pub_string = publication_xml.read()
                publication_soup = BeautifulSoup(pub_string, features="lxml").find('product')
                publication_dict['title_dict']['main_title'] = publication_soup.find('title').find('titletext').text.replace(' (Classic Reprint)', '')
                publication_dict['default_language'] = \
                    publication_soup.find('languagecode').text.lower()
                publication_dict['do_detect_lang'] = False
                publication_dict['rdacarrier'] = 'cr'
                publication_dict['rdamedia'] = 'c'
                publication_dict['rdacontent'] = 'txt'
                publication_dict['LDR_06_07'] = 'am'
                publication_dict['field_007'] = 'cr uuu|||uuuuu'
                publication_dict['field_008_18-34'] = '||||fom||||||| 0|'
                publication_dict['field_006'] = 'm||||fom||||||| 0|'
                publication_dict['fields_590'] = ['Online publication', '2021xhnxfb', 'ebookoa0920']
                publication_dict['isbn'] = [tag.find('idvalue').text for tag in publication_soup.find_all('productidentifier')
                                            if tag.find('productidtype').text == '03'][0]
                publication_dict['original_cataloging_agency'] = 'Forgotten Books'
                publication_dict['title_dict']['sub_title'] = publication_soup.find('title').find('subtitle').text
                publication_dict['authors_list'] = [author_tag.find('keynames').text + ', ' + author_tag.find('namesbeforekey').text for author_tag in publication_soup.find_all('contributor') if author_tag.find('contributorrole').text == 'A01']
                publication_dict['editors_list'] = [author_tag.find('keynames').text + ', ' + author_tag.find('namesbeforekey').text for author_tag in publication_soup.find_all('contributor') if author_tag.find('contributorrole').text != 'A01']
                if publication_soup.find_all('illustrations'):
                    publication_dict['additional_fields'].append({'tag': '300', 'indicators': ['', ''], 'subfields': ['a', '1 online ressource , ' + publication_soup.find('numberofpages').text + ' pp.', 'b', 'illustrations'], 'data': ''})
                else:
                    publication_dict['additional_fields'].append({'tag': '300', 'indicators': ['', ''], 'subfields': ['a', '1 online ressource , ' + publication_soup.find('numberofpages').text + ' pp.'], 'data': ''})
                publication_ids = [tag.find('idvalue').text for tag in publication_soup.find_all('productidentifier') if tag.find('productidtype').text == '01']
                publication_dict['html_links'] = ['https://www.forgottenbooks.com/en/books/' + id for id in publication_ids]
                publication_dict['pdf_links'] = ['https://www.forgottenbooks.com/en/download/' + id + '.pdf' for id in publication_ids]
                if publication_dict['pdf_links'][0] in previously_harvested:
                    continue
                publication_dict['terms_of_use_and_reproduction'] = \
                    {'terms_note':
                         'The e-books may be copied or printed for personal or educational use only. '
                         'None of the e-books or any part of our content may be sold individually or as part of a package, modified in any way or reverse engineered.',
                     'use_and_reproduction_rights': '', 'terms_link': 'https://www.forgottenbooks.com/de/terms'}
                publication_dict['additional_fields'].append({'tag': '650', 'indicators': ['', '7'], 'subfields': ['a', publication_soup.find('basicmainsubject').text, '2', 'bisacsh'], 'data': ''})
                # https://bisg.org/page/History
                try:
                    with urllib.request.urlopen(publication_dict['html_links'][0]) as f:
                        html = gzip.open(f)
                        webpage_soup = BeautifulSoup(html.read(), 'html.parser')
                        info = webpage_soup.find('meta', attrs={'name':'description'})['content']
                        publication_dict['additional_fields'].append({'tag': '698', 'indicators': [' ', ' '], 'subfields': ['a', info], 'data': ''})
                except Exception as e:
                    publication_dict['additional_fields'].append({'tag': '698', 'indicators': [' ', ' '], 'subfields': ['a', publication_dict['html_links'][0]], 'data': ''})
                    write_error_to_logfile.write(e)
                    print(publication_dict['html_links'])
                    continue
                publication_dict['publication_etc_statement']['publication'] = {'place': 'London', 'responsible': 'Forgotten Books', 'country_code': 'enk'}
                publication_dict['publication_year'] = publication_soup.find('publicationdate').text[:4]
                publication_dicts.append(publication_dict)
                nr += 1
            except Exception as e:
                write_error_to_logfile.write(e)
                write_error_to_logfile.comment('Fehler bei der Datei: ' + publication_file)
                items_harvested, publication_dicts = [], []
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Forgotten Books geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'fobo', 'fobo', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/fobo/', 'fobo', 'fobo', create_publication_dicts)
