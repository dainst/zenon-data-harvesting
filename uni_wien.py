import urllib.parse, urllib.request
from bs4 import BeautifulSoup
import re
import urllib.parse, urllib.request
import csv
from bs4 import BeautifulSoup
import create_new_record
from nameparser import HumanName
import find_existing_doublets
import json
import re
import write_error_to_logfile
from harvest_records import harvest_records
from pymarc import MARCReader


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    all_thesis_types = {'dipl': 'Diplomarbeit', 'master': 'Masterarbeit', 'phd': 'Dissertation', 'magister': 'Magisterarbeit'}
    try:
        current_item = 1
        all_publication_urls = []
        urls = ['http://othes.univie.ac.at/view/subjects/15=2E15.html', 'http://othes.univie.ac.at/view/subjects/15=2E16.html',
                'http://othes.univie.ac.at/view/subjects/15=2E17.html', 'http://othes.univie.ac.at/view/subjects/15=2E18.html']
        for url in urls:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                subject_page = response.read()
            subject_page = subject_page.decode('utf-8')
            subject_soup = BeautifulSoup(subject_page, 'html.parser')
            for link in [link for link in [tag['href'] for tag in subject_soup.find_all('a') if 'href' in tag.attrs] if re.findall(r'http://othes\.univie\.ac\.at/\d{1,7}/', link)]:
                all_publication_urls.append(link)
        print(len(all_publication_urls))
        publication_urls = list(set(all_publication_urls))
        print(len(publication_urls))
        for publication_url in publication_urls:
            print(publication_url)
            req = urllib.request.Request(publication_url)
            with urllib.request.urlopen(req) as response:
                publication_page = response.read()
            publication_page = publication_page.decode('utf-8')
            publication_soup = BeautifulSoup(publication_page, 'html.parser')
            if publication_soup.find('meta', attrs={'name': 'eprints.full_text_status'})['content'] != 'public':
                print(publication_soup.find('meta', attrs={'name': 'eprints.full_text_status'}))
                continue
            with open('publication_dict.json', 'r') as publication_dict_template:
                publication_dict = json.load(publication_dict_template)

            publication_dict['doi'] = '10.25365/thesis.' + re.findall(r'\d{1,7}', publication_url)[0]
            publication_dict['title_dict']['main_title'] = publication_soup.find('meta', attrs={'name': 'DC.title'})['content']
            publication_dict['authors_list'] = [author_tag['content'] for author_tag in publication_soup.find_all('meta', attrs={'name': 'DC.creator'})]
            publication_dict['text_body_for_lang_detection'] = publication_soup.find('meta', attrs={'name': 'DC.description'})['content']
            publication_dict['abstract_link'] = publication_url
            publication_dict['publication_year'] = publication_soup.find('meta', attrs={'name': 'DC.date'})['content']
            publication_dict['original_cataloging_agency'] = 'AT-UBW-002'
            publication_dict['fields_590'] = ['Online publication', '2020xhnxuniw', 'ebookoa0420']
            publication_dict['field_300'] = '1 online ressource , ' + publication_soup.find('meta', attrs={'name':'eprints.pages'})['content']
            publication_dict['publication_etc_statement']['publication'] = {'place': 'Wien', 'responsible': 'Universität Wien', 'country_code': 'au '}
            publication_dict['rdacarrier'] = 'cr'
            publication_dict['rdamedia'] = 'c'
            publication_dict['rdacontent'] = 'txt'
            publication_dict['default_language'] = 'ger'
            publication_dict['do_detect_lang'] = True
            publication_dict['LDR_06_07'] = 'am'
            publication_dict['field_007'] = 'cr uuu|||uuuuu'
            publication_dict['field_008_18-34'] = '||||fom||||||| 0|'
            publication_dict['field_006'] = 'm||||fom||||||| 0|'
            publication_dict['pdf_links'].append(publication_soup.find('meta', attrs={'name':'eprints.document_url'})['content'])
            faculty = re.findall('Universität Wien.(.+)BetreuerIn', publication_soup.find('meta', attrs={'name': 'DC.identifier'})['content'].replace('\n', ''))[0].strip()
            subfield_a_502 = all_thesis_types[publication_soup.find('meta', attrs={'name': 'eprints.thesis_type'})['content']] + ', Universität Wien, ' + faculty
            publication_dict['additional_fields'].append({'tag': '502', 'indicators': [' ', ' '],
                                                          'subfields':
                                                              ['a', subfield_a_502,
                                                               'b', all_thesis_types[publication_soup.find('meta', attrs={'name': 'eprints.thesis_type'})['content']],
                                                               'd', publication_dict['publication_year'] + '.'],
                                                          'data': ''})

            publication_dicts.append(publication_dict)
            items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Uni Wien geharvested werden.')
        items_harvested, publication_dicts = [], []
    print(all_thesis_types)
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'univie', 'univie', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/univie/', 'univie', 'univie', create_publication_dicts)

'''
<meta name="eprints.type" content="thesis" />
<meta name="eprints.thesis_type" content="dipl" />

<meta name="DC.subject" content="Archäologie / Bauforschung / Bauforschung / Baukunst / Tivoli / Villa Hadriana / Teatro Marittimo / Römische Geschichte / Hadrian" />
<meta name="DC.subject" content="Archaeology / Architectural history / Tivoli / Villa Hadriana / Teatro Marittimo / Roman history / Hadrian" />


<meta name="DC.identifier" content="   Fiska, Georg  (2012)  Das Teatro Marittimo in der Villa Hadriana.        
Diplomarbeit, Universität Wien.                   Philologisch-Kulturwissenschaftliche Fakultät                
BetreuerIn: Schmidt-Colinet, Andreas       " />


<b>Urheberrechtshinweis</b>: Für Dokumente, die in elektronischer Form über Datennetze angeboten werden, gilt uneingeschränkt das österreichische Urheberrechtsgesetz; insbesondere sind gemäß § 42 UrhG Kopien und Vervielfältigungen nur zum eigenen und privaten Gebrauch gestattet. Details siehe <a href="http://www.ris.bka.gv.at/GeltendeFassung.wxe?QueryID=Bundesnormen&amp;Gesetzesnummer=10001848">Gesetzestext</a>.
'''

# subjects im Thesaurus suchen???

