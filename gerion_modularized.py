import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from nameparser import HumanName
from datetime import datetime
import json
import re
import write_error_to_logfile
import find_sysnumbers_of_volumes
from harvest_records import harvest_records
import gnd_request_for_cor

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        volumes_sysnumbers = find_sysnumbers_of_volumes.find_sysnumbers('000097948')
        url = 'https://revistas.ucm.es/index.php/GERI/issue/archive'
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
        volume_urls = [volume.find('a', class_='cover')['href'] for volume in journal_soup.find_all('div', class_='obj_issue_summary')]
        for volume_url in volume_urls:
            req = urllib.request.Request(volume_url)
            with urllib.request.urlopen(req) as response:
                volume_page = response.read().decode('utf-8')
            volume_soup = BeautifulSoup(volume_page, 'html.parser')
            volume_title = volume_soup.find('div', class_="current_issue_title").text.strip()
            volume_year = re.findall(r'\((\d{4})\)', volume_title)[0]
            if int(volume_year) < 2018:
                break
            if len(volume_title.split(volume_year + ')')) > 1:
                volume_title = 'Gérion - ' + volume_title.split(volume_year + ')')[1].strip(': ') if volume_title.split(volume_year + ')')[1] else 'Gérion'
            else:
                volume_title = 'Gérion'
            article_sections = [section for section in volume_soup.find_all('div', class_="section") if section.find('h2')]
            art_urls, rev_urls = [], []
            article_tags = [section for section in article_sections if 'Artículos' in section.find('h2').text]
            if article_tags:
                art_urls = [article_tag.find('a')['href'] for article_tag in article_tags[0].find_all('div', class_='title')]
            review_tags = [section for section in article_sections if 'Reseñas' in section.find('h2').text]
            if review_tags:
                rev_urls = [review_tag.find('a')['href'] for review_tag in review_tags[0].find_all('div', class_='title')]
            article_urls = art_urls + rev_urls
            for article_url in article_urls:
                req = urllib.request.Request(article_url)
                with urllib.request.urlopen(req) as response:
                    article_page = response.read().decode('utf-8')
                article_soup = BeautifulSoup(article_page, 'html.parser')
                with open('publication_dict.json', 'r') as publication_dict_template:
                    publication_dict = json.load(publication_dict_template)
                publication_dict['volume'] = article_soup.find('meta', attrs={'name': 'citation_volume'})['content']
                publication_dict['issue'] = article_soup.find('meta', attrs={'name': 'citation_issue'})['content']
                current_item = int(volume_year + publication_dict['volume'].zfill(3) + publication_dict['issue'].zfill(2))
                if current_item <= last_item_harvested_in_last_session:
                    break
                publication_dict['rdacontent'] = 'txt'
                publication_dict['rdamedia'] = 'c'
                publication_dict['rdacarrier'] = 'cr'
                publication_dict['authors_list'] = [HumanName(author_tag['content']).last + ', ' + HumanName(author_tag['content']).first
                                                    if gnd_request_for_cor.check_gnd_for_name(author_tag['content']) else author_tag['content']
                                                    for author_tag in article_soup.find_all('meta', attrs={'name': 'citation_author'})]
                publication_dict['host_item']['name'] = volume_title
                publication_dict['volume_year'] = volume_year
                publication_dict['host_item']['sysnumber'] = volumes_sysnumbers[volume_year]
                publication_dict['title_dict']['main_title'] = article_soup.find('meta', attrs={'name': 'citation_title'})['content']
                publication_dict['publication_year'] = article_soup.find('meta', attrs={'name': 'citation_date'})['content'].split('/')[0]
                if article_soup.find('meta', attrs={'name': 'citation_doi'}):
                    publication_dict['doi'] = article_soup.find('meta', attrs={'name': 'citation_doi'})['content']
                publication_dict['abstract_link'] = article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']
                if article_soup.find('meta', attrs={'name': 'citation_pdf_url'}):
                    publication_dict['pdf_links'].append(article_soup.find('meta', attrs={'name': 'citation_pdf_url'})['content'])
                publication_dict['field_300'] = '1 online resource, Fasc. ' + publication_dict['issue'] + ' pp. ' + article_soup.find('meta', attrs={'name': 'citation_firstpage'})['content'] \
                                            + '-' + article_soup.find('meta', attrs={'name': 'citation_lastpage'})['content']
                publication_dict['force_300'] = True
                publication_dict['LDR_06_07'] = 'ab'
                publication_dict['field_006'] = 'm     o  d |      '
                publication_dict['field_007'] = 'cr uuu   uuuuu'
                publication_dict['field_008_18-34'] = 'gr p|o||||||   b|'
                publication_dict['fields_590'] = ['arom', '2020xhnxgeri', 'Online publication']
                publication_dict['original_cataloging_agency'] = 'Universidad Complutense Madrid'
                publication_dict['publication_etc_statement']['publication'] = {'place': 'Madrid',
                                                                                'responsible': 'Universidad Complutense Madrid',
                                                                                'country_code': 'sp '}
                publication_dict['default_language'] = 'es'
                if article_url in rev_urls:
                    publication_dict['review'] = True
                    split_pub = publication_dict['title_dict']['main_title'].split(', ', 1)
                    reviewed_persons = split_pub[0]
                    if re.findall(r'\(=.+?\)', split_pub[1]):
                        title_and_pub = re.split(r'\( *= *.+\)', split_pub[1])
                        publication_info = title_and_pub[1]
                        reviewed_title = title_and_pub[0]
                    elif split_pub[1][0] in ['"', '“']:
                        title_and_pub = [string for string in re.split(r'["|“|”]', split_pub[1]) if string]
                        if len(title_and_pub) < 2:
                            continue
                        reviewed_title = title_and_pub[0]
                        publication_info = title_and_pub[1]
                    else:
                        continue
                    year_of_publication = re.findall(r'\d{4}', publication_info)[0] if re.findall(r'\d{4}', publication_info) else ''
                    reviewed_editors, reviewed_authors = [], []
                    if re.findall(r'\(.+?\)', reviewed_persons):
                        reviewed_persons = re.sub(r'\(.+?\)', '', reviewed_persons)
                        reviewed_persons = reviewed_persons.strip()
                        reviewed_editors = [HumanName(author).last + ', ' + HumanName(author).first if gnd_request_for_cor.check_gnd_for_name(author) else author
                                            for author in re.split(r' *– *', reviewed_persons)]
                    else:
                        reviewed_persons = reviewed_persons.strip()
                        reviewed_authors = [HumanName(author).last + ', ' + HumanName(author).first if gnd_request_for_cor.check_gnd_for_name(author) else author
                                            for author in re.split(r' *– *', reviewed_persons)]
                    publication_dict['review'] = True
                    publication_dict['review_list'].append({'reviewed_title': reviewed_title, 'reviewed_authors': reviewed_authors,
                                                            'reviewed_editors': reviewed_editors, 'year_of_publication': year_of_publication})
                if not publication_dict['review']:
                    publication_dict['text_body_for_lang_detection'] = article_soup.find('div', class_="item abstract").text.replace('Resumen', '').strip() \
                        if article_soup.find('div', class_="item abstract") else publication_dict['title_dict']['main_title']
                    publication_dict['do_detect_lang'] = True
                else:
                    publication_dict['do_detect_lang'] = False
                publication_dicts.append(publication_dict)
                items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Gerion geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'gerion', 'Gerion', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/gerion/', 'gerion', 'Gerion', create_publication_dicts)
