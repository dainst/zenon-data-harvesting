import urllib.parse, urllib.request
from bs4 import BeautifulSoup
from nameparser import HumanName
import create_new_record


def create_review_dict(review_title):
    review_title = review_title.replace(" (review)", "")
    review_list = []
    for title in review_title.split(" and: "):
        new_review = {}
        title=title.strip(",")
        if " ed. by " in title:
            new_review['reviewed_title'], new_review['reviewed_editors'] = title.split(" ed. by ")
            new_review['reviewed_authors'] = ''
        elif " eds. by " in title:
            new_review['reviewed_title'], new_review['reviewed_editors'] = title.split(" eds. by ")
            new_review['reviewed_authors'] = ''
        elif " by " in title:
            new_review['reviewed_title'], new_review['reviewed_authors'] = title.split(" by ")
            new_review['reviewed_editors'] = ''
        else:
            new_review['reviewed_title'], new_review['reviewed_authors'], new_review['reviewed_editors'] = title, [], []
        for responsibles in ['reviewed_editors', 'reviewed_authors']:
            if new_review[responsibles]:
                new_review[responsibles] = [(HumanName(person).last+", "+HumanName(person).first).strip() for person in new_review[responsibles].split(', ')[0].split(' and ')]
        review_list.append(new_review)
    return review_list


out=None
volumes_sysnumbers={'2018': '001559108', '2017': '001521166', '2016': '001470725', '2015':'001433155', '2014': '001479933', '2013': '001376375', '2012': '001325845', '2011': '001316753', '2010': '000846623', '2009':'000810765', '2008':'000804909'}
url = 'https://muse.jhu.edu/journal/399'
user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
values = {'name': 'Helena Nebel',
          'location': 'Berlin',
          'language': 'Python' }
headers = {'User-Agent': user_agent}
data = urllib.parse.urlencode(values)
data = data.encode('ascii')
req = urllib.request.Request(url, data, headers)
with urllib.request.urlopen(req) as response:
    journal_page = response.read()
journal_page=journal_page.decode('utf-8')
journal_soup=BeautifulSoup(journal_page, 'html.parser')
list_elements=journal_soup.find_all('li', class_='volume')
issues=[]
for list_element in list_elements:
    issue_url = 'https://muse.jhu.edu' + str(list_element.span.a).split('"')[1]
    if list_element.span.a.text.replace(' ', '_').split(',')[0] not in issues:
        out=open('records/late_antiquity/'+list_element.span.a.text.replace(' ', '_').split(',')[0]+'.mrc', 'wb')
        issue_nr='1'
    else:
        issue_nr='2'
    issues.append(list_element.span.a.text.replace(' ', '_').split(',')[0])
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
    values = {'name': 'Helena Nebel',
              'location': 'Berlin',
              'language': 'Python' }
    headers = {'User-Agent': user_agent}
    data = urllib.parse.urlencode(values)
    data = data.encode('ascii')
    req = urllib.request.Request(issue_url, data, headers)
    with urllib.request.urlopen(req) as response:
        issue_page = response.read().decode('utf-8')
    issue_soup=BeautifulSoup(issue_page, 'html.parser')
    volume=(issue_soup.find_all('a', href="/journal/399")[1].text[6:].split(",", 1)[0]).strip()
    year=issue_soup.find_all('a', href="/journal/399")[1].text[6:].split(",", 1)[1][-4:]
    articles=issue_soup.find_all('div', class_='card_text')[1:-1]
    for article in articles:
        if year == '2019':
            if article.ol.a.text not in ["Volume Table of Contents", "Volume Contents", "From the Editor", "Bibliography", "From the Guest Editors"]:
                    publication_dict = {'title_dict':
                                            {'main_title': '', 'sub_title': '', 'parallel_title': '', 'other_review_title': ''},
                                            'authors_list': [], 'editors_list': [], 'abstract_link': '', 'table_of_contents_link': '',
                                            'pdf_link': '', 'html_link': '',
                                            'other_links_with_public_note': [{'public_note': '', 'url': ''}], 'doi': '',
                                            'urn': '', 'text_body_for_lang_detection': '', 'fields_590': [],
                                            'original_cataloging_agency': '', 'publication_year': '', 'field_300': '',
                                            'publication_etc_statement':
                                                {'production': {'place': '', 'responsible': '', 'country_code': ''},
                                                 'publication': {'place': '', 'responsible': '', 'country_code': ''},
                                                 'distribution': {'place': '', 'responsible': '', 'country_code': ''},
                                                 'manufacture': {'place': '', 'responsible': '', 'country_code': ''}},
                                            'copyright_statement': {'year': ''},
                                            'rdacontent': '', 'rdamedia': '', 'rdacarrier': '',
                                            'host_item': {'sysnumber': '', 'name': ''}, 'LDR_06_07': '',
                                            'field_006': '', 'field_007': '', 'field_008_18-34': '', 'field_008_06': '',
                                            'additional_fields': {'[placeholder_for_tag_of_field]': {'indicator_1': '',
                                                                                                     'indicator_2': '',
                                                                                                     'subfields':
                                                                                                         {'[subfield_code]': ''}}},
                                            'default_language': '', 'volume': '', 'review': False,
                                        'review_dict':
                                            {'reviewed_title': '', 'reviewed_authors': '',
                                             'year_of _publication': '', 'reviewed_editors': ''}
                                        }

                    publication_dict['table_of_contents_link'] = issue_url
                    for author in article.ol.find('li', class_='author').find_all('a'):
                        name=HumanName(author.text)
                        publication_dict['authors_list'].append((name.last+", "+name.first+" "+name.middle).strip())
                    title=article.ol.a.text
                    if '(review)' in title:
                        publication_dict['review'] = True
                        publication_dict['review_list'] = create_review_dict(title)
                    else:
                        if len(title.split(": ", 1)) > 1:
                            publication_dict['title_dict']['main_title'], publication_dict['title_dict']['sub_title'] = title.split(": ", 1)
                        else:
                            publication_dict['title_dict']['main_title'] = title
                    article_url = 'https://muse.jhu.edu' + str(article.ol.find('li', class_='title').span.a).split('"', 2)[1]
                    publication_dict['abstract_link'] = article_url
                    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
                    values = {'name': 'Helena Nebel',
                              'location': 'Berlin',
                              'language': 'Python' }
                    headers = {'User-Agent': user_agent}
                    data = urllib.parse.urlencode(values)
                    data = data.encode('ascii')
                    req = urllib.request.Request(article_url, data, headers)#
                    with urllib.request.urlopen(req) as response:
                        article_page = response.read().decode('utf-8')
                    article_soup=BeautifulSoup(article_page, 'html.parser')
                    publication_dict['field_300'] = 'Fasc. '+issue_nr+', '+article_soup.find('li', class_='pg').text
                    if article_soup.find('li', class_='doi'):
                        publication_dict['doi'] = article_soup.find('li', class_='doi').a.text
                    publication_dict['LDR_06_07'] = 'ab'
                    publication_dict['fields_590'] = ['arom', '2019xhnxjola']
                    publication_dict['field_007'] = 'ta'
                    publication_dict['publication_year'] = year
                    publication_dict['volume'] = volume
                    publication_dict['host_item'] = {'name': 'Journal of late antiquity', 'sysnumber': '001579957'}
                    publication_dict['default_language'] = 'eng'
                    publication_dict['publication_etc_statement']['publication'] = {'place': 'Baltimore, MD', 'responsible': 'Johns Hopkins University Press', 'country_code': 'mdu'}
                    abstract_tag = article_soup.find_all('div', class_='abstract')[0]
                    publication_dict['text_body_for_lang_detection'] = [p.text for p in abstract_tag.find_all('p')][-1]
                    publication_dict['field_008_06'] = 's'
                    publication_dict['field_008_18-34'] = 'fr |      ||   ||'
                    publication_dict['rdacontent'] = 'txt'
                    publication_dict['rdamedia'] = 'n'
                    publication_dict['rdacarrier'] = 'nc'
                    create_new_record.create_new_record(out, publication_dict)

