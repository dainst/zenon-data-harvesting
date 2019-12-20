import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import re
import write_error_to_logfile
from nameparser import HumanName
import create_new_record
import json
from datetime import datetime

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")


def harvest():
    return_string = ''
    try:
        with open('records/bmcr/bmcr_logfile.json', 'r') as log_file:
            log_dict = json.load(log_file)
            last_item_harvested_in_last_session = log_dict['last_item_harvested']
        pub_nr = 0
        items_harvested = []
        out = open('records/bmcr/bmcr_' + timestampStr + '.mrc', 'wb')
        url = 'http://bmcr.brynmawr.edu/archive.html'
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
        list_elements = journal_soup.find_all('a', class_='style1')
        list_elements = [list_element['href'] for list_element in list_elements if len(re.findall(r'^\d{4}$', list_element.text)) == 1]
        list_elements = [list_element if "http://bmcr.brynmawr.edu/" in list_element else "http://bmcr.brynmawr.edu/" + list_element for list_element in list_elements]
        list_elements = [re.findall(r'(http://bmcr.brynmawr.edu/\d{4}).*$', list_element)[0] for list_element in list_elements]
        issues = []
        for list_element in list_elements:
            url = list_element
            year = re.findall(r'\d{4}', list_element)[0]
            if int(year) < 2019:
                continue
            if re.findall(r'\d{4}', list_element)[0] not in issues:
                issues.append(re.findall(r'\d{4}', list_element)[0])
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
            values = {'name': 'Helena Nebel',
                      'location': 'Berlin',
                      'language': 'Python'}
            headers = {'User-Agent': user_agent}
            data = urllib.parse.urlencode(values)
            data = data.encode('ascii')
            req = urllib.request.Request(url, data, headers)
            with urllib.request.urlopen(req) as response:
                issue_page = response.read()
            issue_soup = BeautifulSoup(issue_page, 'html.parser')
            articles_container = issue_soup.find_all('div', id='indexcontent')
            if len(articles_container) == 1:
                articles = [article for article in articles_container[0].find_all('li') if "Books Received" not in article.text]
                for article in articles:
                    if int(article.find('a').text.replace('.', '')) > last_item_harvested_in_last_session:
                        with open('publication_dict.json', 'r') as publication_dict_template:
                            publication_dict = json.load(publication_dict_template)
                        article_link = article.find('a')['href']
                        req = urllib.request.Request(article_link)
                        with urllib.request.urlopen(req) as response:
                            article_page = response.read()
                        article_soup = BeautifulSoup(article_page, 'html.parser')
                        all_links = [link['href'] for link in article_soup.find_all('a') if 'href' in link.attrs]
                        blog_links = [link for link in all_links if (('www.bmcreview.org' in link) and (all_links.count(link) == 2))]
                        if len(blog_links) == 2:
                            blog_link = blog_links[0]
                        else:
                            blog_link = None
                        review_author = article.text.strip('\n').rsplit('\n', 1)[1].strip('.')
                        review_author_name = review_author.replace('Response by ', '')
                        if 'Reviewed by ' in review_author:
                            review_author_name = review_author.replace('Reviewed by ', '')
                            publication_dict['review'] = True
                        elif 'Response by ' in review_author:
                            review_author_name = review_author.replace('Response by ', '')
                            publication_dict['response'] = True
                        if review_author_name:
                            publication_dict['authors_list'] = [(HumanName(author).last + ', ' + HumanName(author).first + ' ' + HumanName(author).middle).strip() for and_seperated_authors in
                                                                review_author_name.split(', ') for author in and_seperated_authors.split(' and ')]
                            publication_year = ''
                            publication_dict['text_body_for_lang_detection'] = article_soup.find_all('div', property='reviewBody')[0].text
                            if publication_dict['review']:
                                for pub in article_soup.find_all('h3'):
                                    title_reviewed = pub.find_all('i', property='name')[0].text
                                    if re.findall(r'.Bd\..', title_reviewed):
                                        if len(re.findall(r'.Bd\..*?:', title_reviewed)) == 0:
                                            title_reviewed = title_reviewed.rsplit('Bd.', 1)[0]
                                        else:
                                            title_reviewed = title_reviewed
                                    elif re.findall(r'.\..', title_reviewed):
                                        title_reviewed = title_reviewed.rsplit('.', 1)[0]
                                    if pub.find_all('span', property='datePublished'):
                                        publication_year = pub.find_all('span', property='datePublished')[0].text
                                    if pub.find_all('span', property='author'):
                                        author = pub.find_all('span', property='author')[0].text.replace(u'\u200b', '').replace(u'\xa0', '').strip().split(', ')[0]
                                        reviewed_authors = [(HumanName(author).last + ', ' + HumanName(author).first + ' ' + HumanName(author).middle).strip()]
                                    else:
                                        reviewed_authors = []
                                    publication_dict['review_list'].append({'reviewed_title': title_reviewed,
                                                                            'reviewed_authors': reviewed_authors,
                                                                            'reviewed_editors': [],
                                                                            'year_of_publication': publication_year,
                                                                            })
                            else:
                                for h3_tags in article_soup.find_all('h3'):
                                    if type(h3_tags).__name__ != 'list':
                                        links = [a['href'] for a in h3_tags.find_all('a')]
                                    else:
                                        links = [a['href'] for h3 in h3_tags for a in h3.find_all('a')]
                                    for responded_review_link in links:
                                        req = urllib.request.Request(responded_review_link)
                                        with urllib.request.urlopen(req) as response:
                                            responded_review_page = response.read()
                                        responded_review_soup = BeautifulSoup(responded_review_page, 'html.parser')
                                        for resp_rev in responded_review_soup.find_all('h3'):
                                            title_reviewed = resp_rev.find_all('i', property='name')[0].text
                                            if re.findall(r'.Bd\..', title_reviewed):
                                                if len(re.findall(r'.Bd\..*?:', title_reviewed)) == 0:
                                                    title_reviewed = title_reviewed.rsplit('Bd.', 1)[0]
                                                else:
                                                    title_reviewed = title_reviewed
                                            elif re.findall(r'.\..', title_reviewed):
                                                title_reviewed = title_reviewed.rsplit('.', 1)[0]
                                            if resp_rev.find_all('span', property='datePublished'):
                                                publication_year = resp_rev.find_all('span', property='datePublished')[0].text
                                            else:
                                                ''
                                            if resp_rev.find_all('span', property='author'):
                                                reviewed_authors = [resp_rev.find_all('span', property='author')[0].text.replace(u'\u200b', '').replace(u'\xa0', '').strip().split(', ')[0]]
                                            else:
                                                reviewed_authors = []
                                            publication_dict['response_list'].append({'reviewed_title': title_reviewed,
                                                                                      'reviewed_authors': reviewed_authors,
                                                                                      'reviewed_editors': [],
                                                                                      'year_of_publication': publication_year,
                                                                                      })
                        publication_dict['LDR_06_07'] = 'ab'
                        publication_dict['field_006'] = 'm     o  d |      '
                        publication_dict['field_007'] = 'cr  uuu      uuuuu'
                        publication_dict['field_008_18-34'] = 'k| poooo  ||   b|'
                        publication_dict['table_of_contents_link'] = url
                        publication_dict['original_cataloging_agency'] = 'BMCR'
                        publication_dict['publication_etc_statement']['publication'] = {'place': 'Bryn Mawr, PA',
                                                                                        'responsible': 'Thomas Library, Bryn Mawr College',
                                                                                        'country_code': 'pau'}
                        publication_dict['publication_year'] = year
                        publication_dict['field_300'] = '1 online resource'
                        publication_dict['rdacontent'] = 'txt'
                        publication_dict['rdamedia'] = 'c'
                        publication_dict['rdacarrier'] = 'cr'
                        publication_dict['fields_590'] = ['arom', 'Online publication', '2019xhnxbmcr']
                        publication_dict['html_links'].append(article_link)
                        publication_dict['additional_fields'].append({'tag': '856', 'indicators': ['4', '1'],
                                                                      'subfields':
                                                                          ['z', 'BMCR-Blog', 'u', blog_link],
                                                                      'data': ''})
                        publication_dict['host_item'] = {'name': 'Bryn Mawr Classical Review', 'sysnumber': '000810352', 'issn': ''}
                        publication_dict['default_language'] = 'en'
                        if create_new_record.check_publication_dict_for_completeness_and_validity(publication_dict):
                            created = create_new_record.create_new_record(out, publication_dict)
                            items_harvested.append(int(article.find('a').text.replace('.', '')))
                            pub_nr += created
                            print(pub_nr)
                        else:
                            break
        write_error_to_logfile.comment('Letzte geharvestete Publikation von BMCR: ' + str(last_item_harvested_in_last_session))
        return_string += 'Es wurden ' + str(pub_nr) + ' neue Records für BMCR erstellt.'
        if items_harvested:
            with open('records/bmcr/bmcr_logfile.json', 'w') as log_file:
                log_dict = {"last_item_harvested": max(items_harvested)}
                json.dump(log_dict, log_file)
                write_error_to_logfile.comment('Log-File wurde auf ' + str(max(items_harvested)) + ' geupdated.')
    except Exception as e:
        write_error_to_logfile.write(e)
    return return_string


'''bryn m.:
beim nächsten harvesting: eine Statistik ausgeben
- wie viele Datensätze ohne LKR zum rezensierten Werk
- wie viele Datensätze mit  LKR zum rezensierten Werk
- wie viele Datensätze mit  2 LKR-Feldern zum rezensierten Werk , mit
Angabe der ZENON-IDs'''
