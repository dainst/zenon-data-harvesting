from pymarc import MARCReader
import urllib.request
import re
from bs4 import BeautifulSoup
import json
from harvest_records import harvest_records
import write_error_to_logfile

def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        empty_page = False
        page_nr = 1
        while not empty_page:
            url = 'https://books.ub.uni-heidelberg.de/propylaeum/catalog/index?page_nr=' + str(page_nr)
            page_nr += 1
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                series_page = response.read()
            series_page = series_page.decode('utf-8')
            series_soup = BeautifulSoup(series_page, 'html.parser')
            book_tags = [tag.find('article') for tag in series_soup.find_all('div', class_="col-lg-3") if tag.find('article')]
            if not book_tags:
                empty_page = True
            if book_tags:
                links = ['https://books.ub.uni-heidelberg.de' + book_tag.find('a')['href'] for book_tag in book_tags if book_tag.find('a')]
                for link in links:
                    if 'https://doi.org/' in link:
                        continue
                    req = urllib.request.Request(link)
                    with urllib.request.urlopen(req) as response:
                        ebook_page = response.read()
                    ebook_page = ebook_page.decode('utf-8')
                    ebook_soup = BeautifulSoup(ebook_page, 'html.parser')
                    isbn_pdf_list = [re.findall(r'\d{3}-.*\d', tag.text)[0] for tag in ebook_soup.find_all('div', style="margin-top: 0px;") if re.findall(r'\d{3}-.*\d', tag.text)]
                    if not isbn_pdf_list:
                        continue
                    isbn_pdf = isbn_pdf_list[0]
                    publication_date = re.findall(r'(\d{2})\.(\d{2})\.(\d{4})', ebook_soup.find('p',  style="margin-top: 1.2em;").text)[0]
                    current_item = int(publication_date[2] + publication_date[1] + publication_date[0])
                    publication_date = publication_date[2]
                    if current_item > last_item_harvested_in_last_session:
                        current_item = current_item - 1
                        if isbn_pdf:
                            url = u'http://swb.bsz-bw.de/sru/DB=2.1/username=/password=/?query=pica.isb+%3D+"' + isbn_pdf + '"&version=1.1&operation=searchRetrieve&stylesheet=http%3A%2F%2Fswb.bsz-bw.de%2Fsru%2FDB%3D2.1%2F%3Fxsl%3DsearchRetrieveResponse&recordSchema=marc21&maximumRecords=1&startRecord=1&recordPacking=&sortKeys=none&x-info-5-mg-requestGroupings=none'
                            req = urllib.request.Request(url)
                            with urllib.request.urlopen(req) as response:
                                response = response.read()
                            response = BeautifulSoup(response, features='lxml')
                            identifiers = [tag.find('subfield', code='a').text for tag in response.find_all('datafield', tag='035') if tag.find('subfield', code='a')]
                            identifiers_627 = [re.findall(r'\(DE-627\)(.+)$', identifier)[0] for identifier in identifiers if re.findall(r'\(DE-627\)(.+)$', identifier)]
                            if identifiers_627:
                                ppn = identifiers_627[0]
                                webfile = urllib.request.urlopen(
                                    "https://unapi.k10plus.de/?id=gvk:ppn:" + ppn + "&format=marc21")
                                new_reader = MARCReader(webfile)
                                for record in new_reader:
                                    # übernehmen: 003 = original..., 024 (ISBN), 041 (Sprache), 100 teilweise, 245, 264, 300, 490, 830, 502, 689???
                                    delete_fields = [field for field in record.get_fields() if field.tag not in ['003','024', '041', '100', '700', '245', '264', '300', '490', '830', '502', '689']]
                                    [record.remove_field(field) for field in delete_fields]
                                    with open('publication_dict.json', 'r') as publication_dict_template:
                                        publication_dict = json.load(publication_dict_template)
                                    publication_dict['title_dict']['main_title'] = record['245']['a'] if record['245'] and 'a' in record['245'] else ''
                                    publication_dict['title_dict']['sub_title'] = record['245']['b'] if record['245'] and 'b' in record['245'] else ''
                                    publication_dict['title_dict']['responsibility_statement'] = record['245']['c'] if record['245'] and 'c' in record['245'] else ''
                                    publication_dict['authors_list'] = [field['a'] for field in record.get_fields('100', '700')
                                                                        if 'a' in field and field['4'] == 'aut']
                                    publication_dict['editors_list'] = [field['a'] for field in record.get_fields('700')
                                                                        if 'a' in field and field['4'] == 'edt']
                                    publication_dict['abstract_link'] = link
                                    publication_dict['table_of_contents_link'] = link
                                    doi_links = [link for link in [a['href'] for a in ebook_soup.find_all('a') if 'href' in a.attrs] if 'https://doi.org/' in link]
                                    publication_dict['doi'] = doi_links[0].replace('https://doi.org/', '') if doi_links else ''
                                    if publication_dict['doi']:
                                        publication_dict['html_links'].append(doi_links[0])
                                    publication_dict['isbn'] = isbn_pdf
                                    publication_dict['default_language'] = record['041']['a'] if record['041'] else ''
                                    publication_dict['fields_590'] = ['2021xhnxpro', 'Online publication', 'ebookoa0321']
                                    publication_dict['original_cataloging_agency'] = record['003'].data
                                    publication_dict['publication_year'] = publication_date
                                    publication_dict['publication_etc_statement']['publication'] = {'place': 'Heidelberg', 'responsible': 'Propylaeum', 'country_code': 'gw '}
                                    publication_dict['rdacontent'] = 'txt'
                                    publication_dict['rdamedia'] = 'c'
                                    publication_dict['rdacarrier'] = 'cr'
                                    if record['490']:
                                        if record['490']['v']:
                                            if record['490'] and record['830']:
                                                    publication_dict['part_of_series'] = {'series_title': record['490']['a'], 'part': record['830']['v'], 'uniform_title': record['830']['a']}
                                            elif record['490']:
                                                publication_dict['part_of_series'] = {'series_title': record['490']['a'], 'part': record['490']['v'], 'uniform_title': record['490']['a']}
                                    publication_dict['terms_of_use_and_reproduction'] = {'terms_note': 'Creative Commons Namensnennung-Share Alike 4.0 International Public License', 'use_and_reproduction_rights': 'CC BY-SA 4.0', 'terms_link': 'http://creativecommons.org/licenses/by-sa/4.0/'}
                                    publication_dict['LDR_06_07'] = 'am'
                                    publication_dict['field_006'] = 'm     o  d |      '
                                    publication_dict['field_007'] = 'cr uuu   uu|uu'
                                    publication_dict['field_008_18-34'] = '|||||o    |||| 0 '
                                    publication_dicts.append(publication_dict)
                                    items_harvested.append(current_item)
                            else:
                                print('not in swb', link)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Ebooks geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'propylaeum_ebooks', 'Propylaeum Ebooks', create_publication_dicts)
    return return_string

def get_series_names():
    url = 'https://books.ub.uni-heidelberg.de/propylaeum/series'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        series_page = response.read()
    series_page = series_page.decode('utf-8')
    series_soup = BeautifulSoup(series_page, 'html.parser')
    for item in [article for article in series_soup.find_all('article') if not article.find_all('div', class_='post-image')]:
        error = False
        if item.find('h3') and item.find('h4').string:
            print(item.find('h3').string.strip() + ':', item.find('h4').string)
        elif item.find('h3'):
            print(item.find('h3').string.strip())
        else:
            error = True
        print()
        if item.find('span'):
            print('Beschreibung:', item.find('span').string)
        elif item.find('p'):
            print('Beschreibung:', item.find('p').text.strip())
        else:
            error = True
        url = [url for url in item.find_all('a') if 'propylaeum/catalog/series' in url['href']][0]
        print(url)
        print('----')



if __name__ == '__main__':
    # get_series_names()
    harvest_records('records/propylaeum_ebooks/', 'propylaeum_ebooks', 'Propylaeum Ebooks', create_publication_dicts)
