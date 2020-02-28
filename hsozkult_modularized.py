import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import re
import find_reviewed_title
import create_new_record
import json
import write_error_to_logfile
from datetime import datetime, timedelta
import find_existing_doublets
from langdetect import detect
import language_codes
import find_sysnumbers_of_volumes
from harvest_records import harvest_records


# Dubletten werden nicht gefunden. Warum?
# wg LDR != nab, ist naa


def fill_up():
    try:
        with open('records/hsozkult/hsozkult_as_reserve.json', 'r') as hsozkult_as_reserve:
            as_reserve = json.load(hsozkult_as_reserve)
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%d-%b-%Y")
        out = open('records/hsozkult/hsozkult_' + timestampStr + '_fill_up.mrc', 'wb')
        pub_nr = 0
        saved_pub_nr = 1
        new_reserve = []
        for publication_dict in as_reserve:
            reviews = []
            for reviewed_pub in publication_dict['review_list']:
                if reviewed_pub['reviewed_title']:
                    reviews += find_reviewed_title.find(reviewed_pub, publication_dict['publication_year'], 'en')[0]
                    if reviews:
                        create_new_record.create_new_record(out, publication_dict)
                        pub_nr += 1
                    else:
                        all_doublets, additional_physical_form_entrys = \
                                find_existing_doublets.find_review([person.split(', ')[0] for person in (publication_dict['authors_list'] + publication_dict['editors_list'])],
                                                                   publication_dict['publication_year'], 'en', [publication_dict['host_item']['sysnumber']], publication_dict)
                        if not all_doublets:
                            new_reserve.append(publication_dict)
                        saved_pub_nr += 1
        print('Es wurden', pub_nr, 'neue Records für HSozKult erstellt.')
    except Exception as e:
        write_error_to_logfile.write(e)


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        dateTimeObj = datetime.now()
        volumes_sysnumbers = find_sysnumbers_of_volumes.find_sysnumbers('000810356')
        year_to_save_from = int(dateTimeObj.strftime("%Y")) - 3
        page = 1
        harvest_until = int((datetime.now() - timedelta(days=7)).strftime('%Y%m%d'))
        empty_review_page = False
        pub_nr = 0
        saved_pub_nr = 0
        with open('records/hsozkult/hsozkult_as_reserve.json', 'r') as hsozkult_as_reserve:
            as_reserve = json.load(hsozkult_as_reserve)
        basic_url = 'https://www.hsozkult.de/publicationreview/page?page='
        while not empty_review_page:
            if dateTimeObj.strftime("%Y") not in volumes_sysnumbers:
                write_error_to_logfile.comment('Reviews von HSozKult konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr '
                                               + dateTimeObj.strftime("%Y") + ' existiert.')
                write_error_to_logfile.comment('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr ' + dateTimeObj.strftime("%Y") + '.')
                break
            url = basic_url + str(page)
            page += 1
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
            values = {'name': 'Helena Nebel',
                      'location': 'Berlin',
                      'language': 'Python'}
            headers = {'User-Agent': user_agent}
            data = urllib.parse.urlencode(values)
            data = data.encode('ascii')
            page_req = urllib.request.Request(url, data, headers)
            with urllib.request.urlopen(page_req) as page_response:
                hsozkult_page = page_response.read()
            hsozkult_page = hsozkult_page.decode('utf-8')
            journal_soup = BeautifulSoup(hsozkult_page, 'html.parser')
            list_elements = journal_soup.find_all('div', class_="hfn-list-itemtitle")
            list_elements = ['https://www.hsozkult.de'+list_element.find('a')['href'] for list_element in list_elements if list_element.find('a')is not None]
            if not list_elements:
                empty_review_page = True
            for review_url in list_elements:
                with open('publication_dict.json', 'r') as publication_dict_template:
                    publication_dict = json.load(publication_dict_template)
                review_req = urllib.request.Request(review_url)
                with urllib.request.urlopen(review_req) as review_response:
                    review_page = review_response.read()
                review_soup = BeautifulSoup(review_page, 'html.parser')
                day_of_publication, month_of_publication, year_of_publication = \
                    re.findall(r'(\d{2})\.(\d{2})\.(\d{4})', review_soup.find('div', id='hfn-item-citation').text)[0]
                current_item = int(year_of_publication + month_of_publication + day_of_publication)
                if current_item > harvest_until:
                    continue
                if current_item <= last_item_harvested_in_last_session:
                    empty_review_page = True
                    break
                publication_dict['publication_year'] = year_of_publication
                publication_dict['authors_list'] = [author_tag['content'] for author_tag in review_soup.find_all('meta', attrs={'name': 'DC.Creator'})]
                publication_dict['html_links'].append(review_soup.find('meta', attrs={'name': 'DC.Identifier'})['content'])
                publication_dict['text_body_for_lang_detection'] = review_soup.find('div', class_="hfn-item-fulltext").text
                publication_dict['do_detect_lang'] = True
                publication_dict['original_cataloging_agency'] = 'H-Soz-Kult'
                publication_dict['publication_etc_statement']['publication'] = {'place': 'Berlin', 'responsible': 'Humboldt-Universität zu Berlin', 'country_code': 'gw '}
                publication_dict['rdacontent'] = 'txt'
                publication_dict['rdamedia'] = 'c'
                publication_dict['rdacarrier'] = 'cr'
                publication_dict['fields_590'] = ['arom', 'Online publication', '2020xhnxhsoz']
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
                        'Beachten Sie unsere Zitationsregeln:', 'use_and_reproduction_rights': '', 'terms_link': 'https://www.hsozkult.de/copyright'}
                publication_dict['LDR_06_07'] = 'ab'
                publication_dict['field_006'] = 'm     o  d |      '
                publication_dict['field_007'] = 'cr uuu   uu|uu'
                publication_dict['field_008_18-34'] = 'k| p oo|||||   b|'
                mainentity_div_tag = review_soup.find_all('div')[review_soup.find_all('div').index(review_soup.find_all('div', class_="hfn-item-fulltext")[0])+1]
                reviews = []
                nr_reviewed_titles = 0
                for pub in mainentity_div_tag.find_all('span', class_="mainEntity", itemproperty="mainEntity"):
                    nr_reviewed_titles += 1
                    title_reviewed = pub.find('span', itemprop="name").text.strip(' .').strip()
                    publication_year = ''
                    if pub.find_all('span', itemproperty="datePublished"):
                        publication_year = pub.find_all('span', itemproperty="datePublished")[0].text
                    authors_reviewed, editors_reviewed = [], []
                    if pub.find('span', itemprop="author"):
                        authors_reviewed = [author for author in pub.find('span', itemprop="author").text.split('; ')]
                    if pub.find('span', itemprop="editor"):
                        editors_reviewed = [editor.replace(' (Hrsg.)', '') for editor in pub.find('span', itemprop="editor").text.split('; ')]
                    publication_dict['review_list'].append({'reviewed_title': title_reviewed,
                                                            'reviewed_authors': authors_reviewed,
                                                            'reviewed_editors': editors_reviewed,
                                                            'year_of_publication': publication_year,
                                                            })
                    reviews += find_reviewed_title.find({'reviewed_title': title_reviewed,
                                                         'reviewed_authors': authors_reviewed,
                                                         'reviewed_editors': editors_reviewed,
                                                         'year_of_publication': publication_year,
                                                         }, year_of_publication, 'en')[0]
                if reviews:
                    pub_nr += 1
                    publication_dicts.append(publication_dict)
                else:
                    if int(year_of_publication) >= year_to_save_from:
                        language = publication_dict['default_language']
                        if len(re.findall(r'\w', publication_dict['text_body_for_lang_detection'])) >= 50:
                            try:
                                language = \
                                    language_codes.resolve(detect(publication_dict['text_body_for_lang_detection']))
                            except:
                                language = publication_dict['default_language']
                            publication_dict['default_language'] = language
                        else:
                            publication_dict['default_language'] = language
                            publication_dict['do_detect_lang'] = False
                            publication_dict['text_body_for_lang_detection'] = ''
                        as_reserve.append(publication_dict)
                        saved_pub_nr += 1
                        with open('records/hsozkult/hsozkult_as_reserve.json', 'w') as hsozkult_as_reserve:
                            json.dump(as_reserve, hsozkult_as_reserve)
                            write_error_to_logfile.comment('Es wurden ' + str(saved_pub_nr) + ' Rezensionen für die spätere Verwendung gespeichert.')
                items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für HSozKult geharvested werden.')
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'hsozkult', 'HSozKult', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/hsozkult/', 'hsozkult', 'HSozKult', create_publication_dicts)

# nur 3 Jahre speichern, also nichts, was älter ist als 2017.
# Zeitstempelvergleich einführen, sodass alle Reviews, die älter als drei Jahre sind, gelöscht werden!
