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


# Dubletten werden nicht gefunden. Warum?
# wg LDR != nab, ist naa
# Vorgehen bei Mehrfachrezensionen, wenn nur der zweite rezensierte Titel vorhanden ist?

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")

volumes_sysnumbers = {}
page_nr = 0
empty_page = False
while not empty_page:
    page_nr += 1
    volumes_url = 'https://zenon.dainst.org/api/v1/search?lookfor=000810356&type=ParentID&page=' + str(page_nr)
    req = urllib.request.Request(volumes_url)
    with urllib.request.urlopen(req) as response:
        response = response.read()
    response = response.decode('utf-8')
    json_response = json.loads(response)
    # print(json_response)
    if 'records' not in json_response:
        empty_page = True
        continue
    for result in json_response['records']:
        for date in result['publicationDates']:
            volumes_sysnumbers[date] = result['id']
# print(volumes_sysnumbers)

#
def harvest(path):
    return_string = ''
    try:
        days_harvested = []
        year_to_save_from = int(dateTimeObj.strftime("%Y")) - 3
        page = 1
        harvest_until = int((datetime.now() - timedelta(days=7)).strftime('%Y%m%d'))
        with open('records/hsozkult/hsozkult_logfile.json', 'r') as log_file:
            log_dict = json.load(log_file)
            last_day_harvested = log_dict['last_day_harvested']
            print('Letztes geharvestetes Review von HSozKult:', last_day_harvested)
        empty_review_page = False
        pub_nr = 0
        saved_pub_nr = 0
        out = open(path + 'hsozkult_' + timestampStr + '.mrc', 'wb')
        with open('records/hsozkult/hsozkult_as_reserve.json', 'r') as hsozkult_as_reserve:
                as_reserve = json.load(hsozkult_as_reserve)
        #for publication_dict in as_reserve:
            #reviews = []
            #for review in publication_dict['review_list']:
                #if review['reviewed_title']:
                    #reviews += find_reviewed_title.find(review, review['year_of_publication'], 'en')[0]
            #if reviews:
                #create_new_record.create_new_record(out, publication_dict)
                #pub_nr += 1
                #issues_harvested.append(publication_dict['html_links'][0])
                #as_reserve.remove(publication_dict)
            #elif int(publication_dict['publication_year']) < year_to_save_from:
                #as_reserve.remove(publication_dict)
        basic_url = 'https://www.hsozkult.de/publicationreview/page?page='
        while not empty_review_page:
            if dateTimeObj.strftime("%Y") not in volumes_sysnumbers:
                print('Reviews von HSozKult konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr', dateTimeObj.strftime("%Y"), 'existiert.')
                print('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr', dateTimeObj.strftime("%Y"), '.')
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
                days_harvested.append(int(year_of_publication + month_of_publication + day_of_publication))
                print(year_of_publication + month_of_publication + day_of_publication)
                if int(year_of_publication + month_of_publication + day_of_publication) > harvest_until:
                    continue
                if int(year_of_publication + month_of_publication + day_of_publication) <= last_day_harvested:
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
                for pub in mainentity_div_tag.find_all('span', class_="mainEntity", itemproperty="mainEntity"):
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
                    print(reviews)
                    pub_nr += create_new_record.create_new_record(out, publication_dict)
                    #if publication_dict in as_reserve:
                        #as_reserve.remove(publication_dict)
                else:
                    if int(year_of_publication) >= year_to_save_from:
                        language = publication_dict['default_language']
                        if len(re.findall(r'\w', publication_dict['text_body_for_lang_detection'])) >= 50:
                            try:
                                language = \
                                    language_codes.resolve(detect(publication_dict['text_body_for_lang_detection']))
                            except:
                                language = publication_dict['default_language']
                        else:
                            publication_dict['default_language'] = language
                            publication_dict['do_detect_lang'] = False
                            publication_dict['text_body_for_lang_detection'] = ''
                        as_reserve.append(publication_dict)
                        saved_pub_nr += 1
                        print('pub saved:', saved_pub_nr)
        return_string = 'Es wurden ' + str(pub_nr) + ' neue Records für HSozKult erstellt.\n'
        last_day_harvested = max(days_harvested)
        with open('records/hsozkult/hsozkult_logfile.json', 'w') as log_file:
            log_dict = {"last_day_harvested": last_day_harvested}
            json.dump(log_dict, log_file)
            write_error_to_logfile.comment('Log-File wurde auf' + str(last_day_harvested) + 'geupdated.')
        if saved_pub_nr > 0:
            with open('records/hsozkult/hsozkult_as_reserve.json', 'w') as hsozkult_as_reserve:
                json.dump(as_reserve, hsozkult_as_reserve)
                print('Es wurden', saved_pub_nr, 'Rezensionen für die spätere Verwendung gespeichert.')
    except Exception as e:
        write_error_to_logfile.write(e)
    return return_string


def fill_up():
    try:
        with open('records/hsozkult/hsozkult_as_reserve.json', 'r') as hsozkult_as_reserve:
            as_reserve = json.load(hsozkult_as_reserve)
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


if __name__ == '__main__':
    harvest('records/hsozkult/')

# nur 3 Jahre speichern, also nichts, was älter ist als 2017.
# Zeitstempelvergleich einführen, sodass alle Reviews, die älter als drei Jahre sind, gelöscht werden!

# alles im Fachbereich Archäologie: https://www.hsozkult.de/publicationreview/page?sort=newestPublished&fq=category_discip%3A%223/103/127%22
# aktuellen Wert in 'total' mit altem Wert in 'total' vergleichen, dann um die Differenz zurückgehen.
# https://www.hsozkult.de/review/id/reb-2333?title=a-m-de-zayas-a-terrible-revenge&recno=16543&page=828&q=&sort=&fq=&total=16546&subType=reb
# den aktuellen Monat jeweils NICHT abfragen, sondern nur den letzten. Dann ist genau bekannt, ab wo gesammelt werden soll!
