import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import re
import find_reviewed_title
import create_new_record
from pymarc import MARCReader
import json
import handle_error_and_raise
from datetime import datetime

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")

volumes_sysnumbers = {}
volumes_url = 'https://zenon.dainst.org/api/v1/search?lookfor=000810356&type=ParentID'
req = urllib.request.Request(volumes_url)
with urllib.request.urlopen(req) as response:
    response = response.read()
response = response.decode('utf-8')
json_response = json.loads(response)
for result in json_response["records"]:
    webFile = urllib.request.urlopen("https://zenon.dainst.org/Record/"+str(result['id'])+"/Export?style=MARC")
    new_reader = MARCReader(webFile)
    for file in new_reader:
        pub_date = ""
        for field in ['260', '264']:
            if file[field] is not None:
                pub_date = re.findall(r'\d{4}', file[field]['c'])[0]
        volumes_sysnumbers[pub_date] = result['id']

year = dateTimeObj.strftime("%Y")

if year not in volumes_sysnumbers:
    print('Reviews von HSozKult konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr', year, 'existiert.')
    print('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr', year, 'existiert.')


def harvest():
    try:
        with open('records/hsozkult/hsozkult_logfile.json', 'r') as log_file:
            log_dict = json.load(log_file)
            last_item_harvested_in_last_session = log_dict['last_item_harvested']
            print('Letztes geharvestetes Review von HSozKult:', last_item_harvested_in_last_session)
        empty_page = False
        page_nr = 0
        issues_harvested = []
        out = open('records/hsozkult/hsozkult_' + timestampStr + '.mrc', 'wb')
        basic_url = 'https://www.hsozkult.de/publicationreview/page?page='
        while not empty_page:
            page_nr += 1
            url = basic_url + str(page_nr)
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
            values = {'name': 'Helena Nebel',
                      'location': 'Berlin',
                      'language': 'Python'}
            headers = {'User-Agent': user_agent}
            data = urllib.parse.urlencode(values)
            data = data.encode('ascii')
            page_req = urllib.request.Request(url, data, headers)
            with urllib.request.urlopen(page_req) as page_response:
                page = page_response.read()
            page = page.decode('utf-8')
            journal_soup = BeautifulSoup(page, 'html.parser')
            list_elements = journal_soup.find_all('div', class_="hfn-list-itemtitle")
            list_elements = ['https://www.hsozkult.de'+list_element.find('a')['href'] for list_element in list_elements if list_element.find('a')is not None]
            if not list_elements:
                empty_page = True
            for review_url in list_elements:
                with open('publication_dict.json', 'r') as publication_dict_template:
                    publication_dict = json.load(publication_dict_template)
                review_req = urllib.request.Request(review_url)
                with urllib.request.urlopen(review_req) as review_response:
                    review_page = review_response.read()
                review_soup = BeautifulSoup(review_page, 'html.parser')
                year_of_publication = re.findall(r'\d{2}\.\d{2}\.(\d{4})', review_soup.find('div', id='hfn-item-citation').text)[0]
                if int(year_of_publication) > 2018:
                    continue
                print(review_url)
                current_item = int(re.findall(r'id/reb-(\d+)\?', review_url)[0])
                if current_item > last_item_harvested_in_last_session:
                    publication_dict['authors_list'] = [author_tag['content'] for author_tag in review_soup.find_all('meta', attrs={'name': 'DC.Creator'})]
                    publication_dict['html_links'].append(review_soup.find('meta', attrs={'name': 'DC.Identifier'})['content'])
                    publication_dict['text_body_for_lang_detection'] = review_soup.find('div', class_="hfn-item-fulltext").text
                    publication_dict['do_detect_lang'] = True
                    publication_dict['original_cataloging_agency'] = 'H-Soz-Kult'
                    publication_dict['publication_year'] = year_of_publication
                    publication_dict['publication_etc_statement']['publication'] = {'place': 'Berlin', 'responsible': 'Humboldt-Universität zu Berlin', 'country_code': 'gw '}
                    publication_dict['rdacontent'] = 'txt'
                    publication_dict['rdamedia'] = 'c'
                    publication_dict['rdacarrier'] = 'cr'
                    publication_dict['fields_590'] = ['arom', 'Online publication', '2019xhnxhsoz']
                    publication_dict['volume'] = ''
                    publication_dict['volume_year'] = ''
                    publication_dict['issue'] = ''
                    publication_dict['pages'] = ''
                    publication_dict['retro_digitization_info'] = {'place_of_publisher': '', 'publisher': '', 'date_published_online': ''}
                    publication_dict['default_language'] = 'de'
                    publication_dict['review'] = True
                    publication_dict['host_item']['name'] = 'Historische Literatur: Rezensionszeitschrift von H-Soz-u-Kult'
                    publication_dict['host_item']['sysnumber'] = volumes_sysnumbers[publication_dict['publication_year']]
                    publication_dict['host_item']['issn'] = '2196-5307'
                    publication_dict['terms_of_use_and_reproduction'] = \
                        {'terms_note':
                            'Für eine Zweitveröffentlichung von H-Soz-Kult Beiträgen benötigen Sie die Genehmigung sowohl des Autors/der Autorin als auch der Redaktion. '
                            'Beachten Sie unsere Zitationsregeln.', 'use_and_reproduction_rights': '', 'terms_link': 'https://www.hsozkult.de/copyright'}
                    publication_dict['LDR_06_07'] = 'ab'
                    publication_dict['field_006'] = 'm     o  d |      '
                    publication_dict['field_007'] = 'cr uuu   uu|uu'
                    publication_dict['field_008_18-34'] = 'k| p oo|||||   b|'
                    mainentity_div_tag = review_soup.find_all('div')[review_soup.find_all('div').index(review_soup.find_all('div', class_="hfn-item-fulltext")[0])+1]
                    for pub in mainentity_div_tag.find_all('span', class_="mainEntity", itemproperty="mainEntity"):
                        title_reviewed = pub.find('span', itemprop="name").text.strip(' .').strip()
                        publication_year = ''
                        if pub.find_all('span', itemproperty="datePublished"):
                            publication_year = pub.find_all('span', itemproperty="datePublished")[0].text
                        authors_reviewed, editors_reviewed = [], []
                        if pub.find('span', itemprop="author"):
                            authors_reviewed = [author for author in pub.find('span', itemprop="author").text.split('; ')]
                        if pub.find('span', itemprop="editor"):
                            editors_reviewed = [editor for editor in pub.find('span', itemprop="editor").text.split('; ')]
                        publication_dict['review_list'].append({'reviewed_title': title_reviewed,
                                                                'reviewed_authors': authors_reviewed,
                                                                'reviewed_editors': editors_reviewed,
                                                                'year_of_publication': publication_year,
                                                                })
                        reviews = find_reviewed_title.find(title_reviewed, authors_reviewed + editors_reviewed, publication_year, year_of_publication, 'en')
                        if reviews:
                            create_new_record.create_new_record(out, publication_dict)
                            issues_harvested.append(current_item)
    except Exception as e:
        handle_error_and_raise.handle_error_and_raise(e)



# alles im Fachbereich Archäologie: https://www.hsozkult.de/publicationreview/page?sort=newestPublished&fq=category_discip%3A%223/103/127%22
