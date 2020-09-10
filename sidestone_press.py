import urllib.parse, urllib.request
import csv
from bs4 import BeautifulSoup
from nameparser import HumanName
import json
import re
import write_error_to_logfile
from harvest_records import harvest_records
import gnd_request_for_cor


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        current_item = 1
        with open("sidestonepress.csv", "r") as link_table:
            reader = csv.reader(link_table, delimiter=';')
            row_nr = 0
            for row in reader:
                row_nr += 1
                if row_nr > 1:
                    url = row[9]
                    print(url)
                    req = urllib.request.Request(url)
                    with urllib.request.urlopen(req) as response:
                        book_page = response.read()
                    book_page = book_page.decode('utf-8')
                    book_soup = BeautifulSoup(book_page, 'html.parser')
                    with open('publication_dict.json', 'r') as publication_dict_template:
                        publication_dict = json.load(publication_dict_template)
                    title = book_soup.find('meta', attrs={'name':'citation_title'})['content'].strip()
                    responisibility_statement = book_soup.find('meta', attrs={'name':'citation_author'})['content']
                    publication_dict['text_body_for_lang_detection'] = book_soup.find('meta', attrs={'name':'description'})['content']
                    responisibility_statement = responisibility_statement.split(', with contributions by')[0].split(', met bijdragen van')[0].split(' (edited by')[0]
                    for responsibility_word in ['Edited by ', 'edited by ', ' (ed.)', 'Introduction, translation and discussion ']:
                        if responsibility_word in responisibility_statement:
                            publication_dict['editors_list'] = [HumanName(e).last + ', ' +HumanName(e).first if not gnd_request_for_cor.check_gnd_for_name(e) else e
                                                                for editor in responisibility_statement.replace(responsibility_word, '').split(', and ') for edit in editor.split(' & ') for ed in edit.split(', ') for e in ed.split(' and ')]
                            break
                    for responsibility_word in ['Redactie: ', 'Onder redactie van ', 'Uitgegeven door ', 'Bewerkt door ', 'Bezorgd door ']:
                        if responsibility_word in responisibility_statement:
                            publication_dict['editors_list'] = [HumanName(edit).last + ', ' + HumanName(edit).first if not gnd_request_for_cor.check_gnd_for_name(edit) else edit for editor in responisibility_statement.replace(responsibility_word, '').split(' en ') for edit in editor.split(', ')]
                            break
                    if not publication_dict['editors_list']:
                        publication_dict['authors_list'] = [HumanName(ed).last + ', ' + HumanName(ed).first if not gnd_request_for_cor.check_gnd_for_name(ed) else ed for editor in responisibility_statement.replace(responsibility_word, '').split(' & ') if responisibility_statement for edit in editor.split(' en ') for ed in edit.split(', ')]
                    sub_title = ''
                    if '. ' in title:
                        if ' av. n. è.' in title and 'Ldkr. ' in title and ' (c. ' in title:
                            main_title, sub_title = '. '.join(title.split('. ', 2)[:2]), title.split('. ', 2)[2]
                        else:
                            main_title, sub_title = title.split('. ', 1)
                    else:
                        main_title = title
                    publication_dict['title_dict']['main_title'] = main_title.strip()
                    if sub_title:
                        publication_dict['title_dict']['sub_title'] = sub_title.strip()
                    publication_dict['abstract_link'] = url
                    publication_dict['table_of_contents_link'] = url
                    if book_soup.find('a', class_='hide-for-large expanded small hollow buy button elibrarymediumsmall blacklabel'):
                        publication_dict['html_links'].append(book_soup.find('a', class_='hide-for-large expanded small hollow buy button elibrarymediumsmall blacklabel')['href'])
                    publication_dict['fields_590'] = ['Online publication', '2020xhnxsistk', 'ebook0420']
                    publication_dict['original_cataloging_agency'] = 'Sidestone Press'
                    publication_dict['publication_year'] = re.findall(r'\d{4}', book_soup.find('meta', attrs={'name':'citation_publication_date'})['content'])[0]
                    publication_dict['field_300'] = '1 online ressource'
                    publication_dict['publication_etc_statement']['publication'] = {'place': 'Leiden', 'responsible': book_soup.find('meta', attrs={'name':'publisher'})['content'], 'country_code': 'ne '}
                    publication_dict['rdacarrier'] = 'cr'
                    publication_dict['rdamedia'] = 'c'
                    publication_dict['rdacontent'] = 'txt'
                    publication_dict['LDR_06_07'] = 'am'
                    publication_dict['field_007'] = 'cr uuu|||uuuuu'
                    publication_dict['field_008_18-34'] = '||||fo|||||||| 0|'
                    publication_dict['field_006'] = 'm||||fo|||||||| 0|'
                    publication_dict['default_language'] = 'eng'
                    publication_dict['do_detect_lang'] = True

                    publication_dict['isbn'] = book_soup.find('meta', attrs={'name':'citation_isbn'})['content']
                    if len(publication_dict['isbn']) not in [10,13]:
                        print('journal', url)
                        continue
                    if book_soup.find('a', class_='expanded small hollow buy button blacklabel'):
                        publication_dict['pdf_links'].append('https://www.sidestone.com' + book_soup.find('a', class_='expanded small hollow buy button blacklabel')['href'])
                    publication_dicts.append(publication_dict)
                    items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Sidestone geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'sidestone', 'sidestone', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/sidestone/', 'sidestone', 'sidestone', create_publication_dicts)
