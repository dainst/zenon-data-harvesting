import urllib.parse
import urllib.request
import re
from bs4 import BeautifulSoup
from _datetime import datetime
import json
import create_new_record
import write_error_to_logfile

# bearbeiten, Titel kann nicht ausgelesen werden!

def harvest(path):
    pub_nr = 0
    return_string = ''
    try:
        publishers = {'1885': ['Berlin', 'Georg Reimer'], '1919': ['Berlin; Leipzig', 'Walter de Gruyter & Co.']}
        years_published_in = [int(year) for year in list(publishers.keys())]
        years_published_in.sort(reverse=True)

        datetimeobj = datetime.now()
        timestamp = datetimeobj.strftime("%d-%b-%Y")

        with open('records/jdi/jdi_logfile.json', 'r') as log_file:
            log_dict = json.load(log_file)
            last_issue_harvested_in_last_session = log_dict['last_issue_harvested']
        issues_harvested = []
        out = open(path + 'jdi_' + timestamp + '.mrc', 'wb')
        basic_url = 'https://digi.ub.uni-heidelberg.de/diglit/jdi'
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
        values = {'name': 'Helena Nebel',
                  'location': 'Berlin',
                  'language': 'Python'}
        headers = {'User-Agent': user_agent}
        data = urllib.parse.urlencode(values)
        data = data.encode('ascii')
        req = urllib.request.Request(basic_url, data, headers)
        with urllib.request.urlopen(req) as response:
            yearbook_page = response.read()
        pub_nr = 0
        volume_nr = 0
        yearbook_page = yearbook_page.decode('utf-8')
        yearbook_page = BeautifulSoup(yearbook_page, 'html.parser')
        volume_years = [item.find('a').text for item in yearbook_page.find('table', class_='tabelle-baendeliste').find_all('td') if item.find('a')]
        volume_urls = [item['href'] for item in yearbook_page.find('table', class_='tabelle-baendeliste').find_all('a')]
        for volume_url in volume_urls:
            req = urllib.request.Request(volume_url, data, headers)
            with urllib.request.urlopen(req) as response:
                volume_page = response.read()
            volume_page = volume_page.decode('utf-8')
            volume_soup = BeautifulSoup(volume_page, 'html.parser')
            date_published_online = re.findall(r'\d{4}', volume_soup.find('div', id='publikationsdatum').text)[0]
            volume_title = volume_years[volume_nr]
            volume_nr += 1
            print(volume_title)
            if re.findall(r'(\d{1,3}/\d{1,3})\.', volume_title.strip()):
                volume = re.findall(r'(\d{1,3})\.', volume_title)[0]
            else:
                volume = re.findall(r'(\d{1,3})\.', volume_title)[0]
            if re.findall(r'(\d{4}/\d{4})', volume_title.strip()):
                volume_year = re.findall(r'(\d{4}/\d{4})', volume_title)[0]
            else:
                volume_year = re.findall(r'(\d{4})', volume_title)[0]
            current_item = int(volume_year.split('/')[0] + volume.split('/')[0].zfill(3))
            print(current_item, last_issue_harvested_in_last_session)
            if current_item > last_issue_harvested_in_last_session:
                mets_url = volume_url.split("?")[0]+'/mets'
                xml_file = urllib.request.urlopen(mets_url)
                xml_soup = BeautifulSoup(xml_file, 'xml')
                for article_xml in xml_soup.find_all('mods:mods')[1:]:
                    if article_xml.find('mods:identifier', type='doi') and article_xml.find('mods:title').text not in ['Inhalt', 'Register']:
                        with open('publication_dict.json', 'r') as publication_dict_template:
                            publication_dict = json.load(publication_dict_template)
                        publication_dict['title_dict']['main_title'] = article_xml.find('mods:title').text
                        publication_dict['authors_list'] = list(dict.fromkeys([authors_tag.find('mods:displayForm').text
                                                                               for authors_tag in [authors_tag for authors_tag in article_xml.find_all('mods:name')
                                                                                                   if authors_tag.find('mods:roleTerm')] if authors_tag.find('mods:roleTerm').text == 'aut']))
                        publication_dict['editors_list'] = list(dict.fromkeys([authors_tag.find('mods:displayForm').text
                                                                               for authors_tag in [authors_tag for authors_tag in article_xml.find_all('mods:name')
                                                                                                   if authors_tag.find('mods:roleTerm')] if authors_tag.find('mods:roleTerm').text == 'edt']))
                        publication_dict['table_of_contents_link'] = volume_url
                        publication_dict['doi'] = article_xml.find('mods:identifier', type='doi').text
                        publication_dict['html_links'].append('https://www.doi.org/' + publication_dict['doi'])
                        publication_dict['other_links_with_public_note'].append({'public_note': '', 'url': ''})
                        publication_dict['default_language'] = 'ger'
                        publication_dict['do_detect_lang'] = False
                        publication_dict['fields_590'] = ['arom', '2020xhnxjdi', 'Online publication']
                        publication_dict['original_cataloging_agency'] = 'DE-16'
                        publication_dict['publication_year'] = re.findall(r'\d{4}', xml_soup.find_all('mods:mods')[0].find('mods:originInfo').find('mods:dateIssued', keyDate='yes').text)[0]
                        place_of_publication = ''
                        publisher = ''
                        for key in years_published_in:
                            if int(publication_dict['publication_year']) >= key:
                                place_of_publication = publishers[str(key)][0]
                                publisher = publishers[str(key)][1]
                                break
                        publication_dict['publication_etc_statement']['publication'] = {'place': place_of_publication, 'responsible': publisher, 'country_code': 'gw '}
                        publication_dict['rdacontent'] = 'txt'
                        publication_dict['rdamedia'] = 'c'
                        publication_dict['rdacarrier'] = 'cr'
                        if int(publication_dict['publication_year']) < 1918:
                            publication_dict['host_item']['name'] = 'Jahrbuch des Kaiserlich Deutschen Archäologischen Instituts'
                        else:
                            publication_dict['host_item']['name'] = 'Jahrbuch des Deutschen Archäologischen Instituts'
                        publication_dict['host_item']['sysnumber'] = '001578267'
                        publication_dict['volume'] = xml_soup.find_all('mods:mods')[0].find('mods:number').text
                        publication_dict['volume_year'] = volume_year
                        publication_dict['pages'] = [pages.find('mods:extent', unit="pages").text for pages in article_xml.find_all('mods:physicalDescription')][0] \
                            if [pages.find('mods:extent', unit="pages") for pages in article_xml.find_all('mods:physicalDescription') if pages.find('mods:extent', unit="pages")] else ''
                        publication_dict['retro_digitization_info'] = {'place_of_publisher': 'Heidelberg', 'publisher': 'Heidelberg UB', 'date_published_online': date_published_online}
                        publication_dict['terms_of_access'] = {'restrictions': '', 'terms_note': '', 'authorized_users': '', 'terms_link': ''}
                        publication_dict['terms_of_use_and_reproduction'] = {'terms_note': 'Lizenz: Freier Zugang - alle Rechte vorbehalten', 'use_and_reproduction_rights': '',
                                                                             'terms_link': 'https://www.ub.uni-heidelberg.de/helios/digi/nutzung/Welcome.html'}
                        publication_dict['LDR_06_07'] = 'ab'
                        publication_dict['field_007'] = 'cr uuu   uuauu'
                        publication_dict['field_006'] = 'm     o  d |      '
                        publication_dict['field_008_18-34'] = 'ar poo||||||   b|'
                        if create_new_record.check_publication_dict_for_completeness_and_validity(publication_dict):
                            created = create_new_record.create_new_record(out, publication_dict)
                            issues_harvested.append(current_item)
                            pub_nr += created
                        else:
                            break

        return_string = 'Es wurden' + str(pub_nr) + 'neue Records für Jahrbuch des Deutschen Archäologischen Instituts erstellt.'
        if issues_harvested:
            with open('records/jdi/jdi_logfile.json', 'w') as log_file:
                log_dict = {"last_issue_harvested": max(issues_harvested)}
                json.dump(log_dict, log_file)
                write_error_to_logfile.comment('Log-File wurde auf' + str(max(issues_harvested)) + 'geupdated.')

    except Exception as e:
        write_error_to_logfile.write(e)
    return return_string


if __name__ == '__main__':
    datetimeobj = datetime.now()
    timestamp = datetimeobj.strftime("%d-%b-%Y")
    harvest('records/jdi/jdi_' + timestamp + '.mrc')
