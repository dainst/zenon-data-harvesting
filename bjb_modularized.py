import urllib.parse
import urllib.request
import language_codes
from bs4 import BeautifulSoup
import spacy
import re
from datetime import datetime
import json
from nameparser import HumanName
import create_new_record
import handle_error_and_raise

def harvest():
    try:
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%d-%b-%Y")
        issues_harvested = []

        with open('records/bjb/bjb_logfile.json', 'r') as log_file:
            log_dict = json.load(log_file)
            last_item_harvested_in_last_session = log_dict['last_issue_harvested']
            print('Letztes geharvestetes Heft von Bonner Jahrbücher:', last_item_harvested_in_last_session)

        producers = {'138': ['Darmstadt', "L.C. Wittich'sche Hofbuchdruckerei"],
                     '106': ['Bonn', "A. Marcus und E. Weber's"],
                     '084': ['Bonn', 'Adolph Marcus'],
                     '003': ['Bonn', 'A. Marcus'],
                     '001': ['Cöln', 'F.C. Eisen']}

        publishers = {'1949': ['Kevelaer Rhld.', 'Butzon & Bercker'],
                      '1948': ['Düsseldorf', 'L. Schwann'],
                      '1933': ['Darmstadt', '[Verein von Altertumsfreunden im Rheinlande]'],
                      '1932': ['Bonn ; Darmstadt', 'Gebr. Scheuer'],
                      '1928': ['Bonn', 'Universitätsbuchdruckerei Gebr. Scheur'],
                      '1927': ['Köln', 'Albert Ahn'],
                      '1921': ['Bonn', "A. Marcus und E. Weber's"],
                      '1840': ['Bonn', '[Verein von Altertumsfreunden im Rheinlande]']}

        years_published_in = [int(year) for year in list(publishers.keys())]
        years_published_in.sort(reverse=True)
        years_produced_in = [int(producer_key) for producer_key in list(producers.keys())]
        years_produced_in.sort(reverse=True)

        exclude_titles = ["Renate Bol, with the collaboration of Simone Frede and Patrick Schollmeyer, and contributions by Anke Ahle, Ute Bolender, Georg Breitner, Friederike Fless, Wolfgang Günther, "
                          "Huberta Heres, Nike Meissner, S. Felicia Meynersen, Carsten Schneider and Berthold F. Weber, "
                          "Marmorskulpturen der römischen Kaiserzeit aus Milet. Aufstellungskontext und programmatische Aussage",
                          "Gérard Moitrieux unter Mitarbeit von Jean-Noël Castorio, Toul et la cité des Leuques. Nouvel Espérandieu"]

        out = open('records/bjb/bjb_' + timestampStr + '.mrc', 'wb')
        basic_url = 'https://journals.ub.uni-heidelberg.de/index.php/bjb/issue/archive/'
        pub_nr = 0
        empty_page = False
        page = 0
        while not empty_page:
            page += 1
            url = basic_url + str(page)
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
            list_elements = journal_soup.find_all('a', class_='title')
            if not list_elements:
                empty_page = True
            for list_element in list_elements:
                issue_information = list_element.text
                issue_url = list_element['href']
                user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
                values = {'name': 'Helena Nebel',
                          'location': 'Berlin',
                          'language': 'Python'}
                headers = {'User-Agent': user_agent}
                data = urllib.parse.urlencode(values)
                data = data.encode('ascii')
                req = urllib.request.Request(issue_url, data, headers)
                with urllib.request.urlopen(req) as response:
                    issue_page = response.read().decode('utf-8')
                issue_soup = BeautifulSoup(issue_page, 'html.parser')
                volume_title = issue_soup.find('title').text
                if "Beilage" not in volume_title:
                    if re.findall(r'(\d{1,3}/\d{1,3})\.', volume_title.strip()):
                        volume = re.findall(r'(\d{1,3}/\d{1,3})\.', volume_title)[0]
                    elif re.findall(r'(\d{1,3}/\d{1,3}) \(', volume_title.strip()):
                        volume = re.findall(r'(\d{1,3}/\d{1,3}) \(', volume_title)[0]
                    elif re.findall(r'( \d{1,3})\.', volume_title.strip()):
                        volume = re.findall(r'(\d{1,3})\.', volume_title)[0]
                    else:
                        volume = re.findall(r' (\d{1,3}) \(', volume_title)[0]
                else:
                    continue
                volume_name = volume_title.split(": ")[1].split("|")[0].strip()
                volume_year = str(min([int(year) for year in re.findall(r'\d{4}', volume_title)]))
                current_item = int(volume_year + volume.split('/')[0].zfill(3))
                print(current_item, volume)
                if current_item > last_item_harvested_in_last_session:
                    if int(volume_year) + 3 > int(dateTimeObj.strftime("%Y")):
                        continue
                        # die Bände werden erst drei Jahre nach dem Druck Open Access online publiziert.
                    if int(volume_year) < 2011:
                        break
                    for article in issue_soup.find_all('div', class_='obj_article_summary'):
                        title = article.find('div', class_='title')
                        article_url = title.find('a')['href']
                        req = urllib.request.Request(article_url, data, headers)
                        with urllib.request.urlopen(req) as response:
                            article_page = response.read().decode('utf-8')
                        article_soup = BeautifulSoup(article_page, 'html.parser')
                        category = article_soup.find('meta', attrs={'name': 'DC.Type.articleType'})['content']
                        if category not in ['Titel', 'Inhalt', 'Verbesserungen', 'Vorwort/Widmung', 'Abkürzungen']:
                            with open('publication_dict.json', 'r') as publication_dict_template:
                                publication_dict = json.load(publication_dict_template)
                            publication_dict['publication_year'] = article_soup.find('meta', attrs={'name': 'citation_date'})['content']
                            if category in ['Bildbeilage', 'Register', 'Miszellen', 'Chronik', 'Vereinsangelegenheiten_Statuten', 'Jahresberichte']:
                                publication_dict['title_dict']['main_title'] = \
                                    article_soup.find('meta', attrs={'name': 'citation_title'})['content'].replace("...", "") + ' ' + volume_name + ', ' + volume + ' (' + volume_year + ')'
                            else:
                                publication_dict['title_dict']['main_title'] = article_soup.find('meta', attrs={'name': 'citation_title'})['content'].replace("...", "")
                            publication_dict['title_dict']['sub_title'] = ''
                            publication_dict['title_dict']['parallel_title'] = ''
                            publication_dict['title_dict']['responsibility_statement'] = ''
                            publication_dict['authors_list'] = [HumanName(author['content']).last + ', ' + HumanName(author['content']).first
                                                                for author in article_soup.find_all('meta', attrs={'name': 'citation_author'}) if author['content'] != "Die Redaktion"]
                            publication_dict['editors_list'] = []
                            publication_dict['abstract_link'] = article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']
                            publication_dict['table_of_contents_link'] = issue_url
                            publication_dict['pdf_links'].append(article_soup.find('meta', attrs={'name': 'citation_pdf_url'})['content'])
                            publication_dict['other_links_with_public_note'].append({'public_note': '', 'url': ''})
                            publication_dict['doi'] = article_soup.find('meta', attrs={'name': 'citation_doi'})['content']
                            publication_dict['text_body_for_lang_detection'] = article_soup.find('meta', attrs={'name': 'DC.Description'})['content']
                            if int(publication_dict['publication_year']) > 2013:
                                publication_dict['field_007'] = 'cr uuu   uu|uu'
                                publication_dict['default_language'] = language_codes.resolve(article_soup.find('meta', attrs={'name': 'DC.Language'})['content'])
                                publication_dict['publication_etc_statement']['publication'] = {'place': 'Heidelberg', 'responsible': 'Propylaeum', 'country_code': 'gw '}
                                publication_dict['do_detect_lang'] = False
                            else:
                                publication_dict['field_007'] = 'cr uuu   uuauu'
                                place_of_publication = ''
                                place_of_production = ''
                                publisher = ''
                                producer = ''
                                for key in years_published_in:
                                    if int(publication_dict['publication_year']) >= key:
                                        place_of_publication = publishers[str(key)][0]
                                        publisher = publishers[str(key)][1]
                                        break
                                for key in years_produced_in:
                                    if int(volume) >= key:
                                        place_of_production = producers[str(key)][0]
                                        producer = producers[str(key)][1]
                                        break
                                publication_dict['retro_digitization_info'] = \
                                    {'place_of_publisher': 'Heidelberg', 'publisher': 'Heidelberg UB',
                                     'date_published_online': article_soup.find('div', class_='published').find('div', class_='value').text.strip()}
                                publication_dict['default_language'] = 'de'
                                publication_dict['publication_etc_statement']['publication'] = {'place': place_of_publication, 'responsible': publisher, 'country_code': ''}
                                publication_dict['publication_etc_statement']['production'] = {'place': place_of_production, 'responsible': producer, 'country_code': ''}
                            publication_dict['language_field'] = {'language_of_resource': [], 'language_of_original_item': []}
                            publication_dict['fields_590'] = ['arom', '2019xhnxbjb', 'Online publication']
                            publication_dict['original_cataloging_agency'] = 'DE-16'
                            if re.findall(r'\d{4}', article_soup.find('meta', attrs={'name': 'DC.Rights'})['content']):
                                publication_dict['copyright_year'] = re.findall(r'\d{4}', article_soup.find('meta', attrs={'name': 'DC.Rights'})['content'])[0]
                            publication_dict['rdacontent'] = 'txt'
                            publication_dict['rdamedia'] = 'c'
                            publication_dict['rdacarrier'] = 'cr'
                            publication_dict['host_item']['name'] = volume_name
                            publication_dict['host_item']['sysnumber'] = '001578364'
                            publication_dict['volume'] = volume
                            publication_dict['volume_year'] = volume_year
                            publication_dict['LDR_06_07'] = 'ab'
                            publication_dict['field_006'] = 'm     o  d |      '
                            publication_dict['field_008_18-34'] = 'ar poo||||||   b|'
                            print(category)
                            if category in ["Litteratur", "Besprechungen"]:
                                not_human_name = "Römisch-germanische Kommission des Deutschen Archaeologischen Instituts"
                                if title not in ["Nachtrag zur Anzeige der in der Hermes’schen Schrift 'Die Neuerburg an der Wied' angeregten Frage: Wer war Heinrich von Ofterdingen?",
                                                 "Rheinische Bibliographie", "Litteratur", "Bemerkungen zu der bei Gall in Trier erschienenen Schrift des Dr. Jacob Schneider",
                                                 "Bemerkungen über das römische Baudenkmal zu Fliessem, in Bezug auf die, im IV. Hefte dieser Jahrbücher, erschienene Recension"]:
                                    title_nr = -1
                                    year_of_reviewed_title = re.findall(r'[^-](\d{4})[^-]', publication_dict['text_body_for_lang_detection'])
                                    for title in publication_dict['title_dict']['main_title'].split("/"):
                                        title_nr += 1
                                        if title not in exclude_titles:
                                            review = True
                                            authors = []
                                            editors = []
                                            if title_nr < len(year_of_reviewed_title):
                                                year = year_of_reviewed_title[title_nr]
                                            else:
                                                year = ''
                                            for editorship_word in ["(éditeurs)", "(editeurs)", "(Herausgeber)", "(editore)", "(editrice)", "(editors)", "(editori)", "(editor)"]:
                                                if editorship_word in title:
                                                    editors_string, title = title.split(editorship_word)
                                                    editors_string = editors_string.strip()
                                                    title = title.strip(", ").strip()
                                                    for separation_word in [" und ", " et ", " and ", " e "]:
                                                        if separation_word in editors_string:
                                                            editors = \
                                                                [HumanName(edit).last + ', ' + HumanName(edit).first for editor in editors_string.split(', ') for edit in editor.split(separation_word)]
                                                    break
                                            title = title.strip()
                                            parts = [title]
                                            if not editors:
                                                if any(word in title for word in [" und ", " et ", " and ", " e "]):
                                                    for separation_word in [" und ", " et ", " and ", " e "]:
                                                        if separation_word in title:
                                                            parts = [part for part in title.split(separation_word)]
                                                            if ', ' in parts[1]:
                                                                abbreviation_nr = \
                                                                    len([abbreviation for abbreviation in re.findall(r'[A-Z]\.', parts[1].split(', ', 1)[0])]) + parts[1].split(', ', 1)[0].count(' von ')
                                                                if len(parts[1].split(', ', 1)[0].split()) - abbreviation_nr in [2, 3]:
                                                                    wrong = [part for part in parts[0].split(', ') if len(part.split()) - part.count(' von ') not in [2, 3]]
                                                                    if not wrong:
                                                                        parts = [parts[0]] + [separation_word.join(parts[1:])]
                                                                        title = parts[1].split(', ', 1)[1]
                                                                        authors = [parts[1].split(', ', 1)[0]] + parts[0].split(', ')
                                                                    else:
                                                                        parts = [title]
                                                                else:
                                                                    parts = [title]
                                                            else:
                                                                parts = [title]
                                                                sep = False
                                                            if len(parts) > 1:
                                                                break
                                                if ', ' in title and len(parts) == 1:
                                                    abbreviation_nr = len([abbreviation for abbreviation in re.findall(r'[A-Z]\.', title.split(', ', 1)[0])]) + title.split(', ', 1)[0].count(' von ')
                                                    if len(title.split(', ', 1)[0].split()) - abbreviation_nr in [2, 3]:
                                                        authors, title = title.split(', ', 1)
                                                        authors = [authors]
                                            authors = [HumanName(author).last + ', ' + HumanName(author).first for author in authors]
                                            publication_dict['review'] = True
                                            publication_dict['review_list'].append({'reviewed_title': title,
                                                                                    'reviewed_authors': authors,
                                                                                    'reviewed_editors': editors,
                                                                                    'year_of_publication': year,
                                                                                    })
                            if create_new_record.check_publication_dict_for_completeness_and_validity(publication_dict):
                                created = create_new_record.create_new_record(out, publication_dict)
                                issues_harvested.append(current_item)
                                pub_nr += created
                            else:
                                break

        print('Es wurden', pub_nr, 'neue Records für Bonner Jahrbücher erstellt.')
        if issues_harvested:
            with open('records/bjb/bjb_logfile.json', 'w') as log_file:
                log_dict = {"last_issue_harvested": max(issues_harvested)}
                json.dump(log_dict, log_file)
                print('Log-File wurde auf', max(issues_harvested), 'geupdated.')

    except Exception as e:
        handle_error_and_raise.handle_error_and_raise(e)


# Lücke zwischen 1933 und 1986 beachten!!!
# bis wann harvesten?

editorship_words_old = ["Hrsg, von ", "Hrsg. von ", "Herausgegeben von ", "hrsg. von ", "herausgegeben von ", "herausg. von ", "Herausgegeb. von ", "; edd. ",
                        " bearbeitet von ", "Aus den Quellen bearbeitet von ", "mit Text von ", "Mit Einleitung, Commentar und zwei Karten versehen von ",
                        "Den Herrn H. Meyer und H. Koechly gewidmet von ", "Zusammengestellt von ",
                        "Aufgenommen und gezeichnet v. ", "Zusammengestellt von ", "Beschrieben und durch XXVI Tafeln erläutert von ", "Erläutert von ", "pubblicata da ", "collegit ",
                        "publié par ", "; edd. ", " Mit Einleitung, Commentar und zwei Karten versehen von "]
old_responsibility_word = ["Beschrieben von ", "Aus den Quellen bearbeitet von ", "mit Text von ", "Mit Einleitung, Commentar und zwei Karten versehen von ",
                           "Den Herrn H. Meyer und H. Koechly gewidmet von ",
                           "Aufgenommen und gezeichnet v. ", "Beschrieben und durch XXVI Tafeln erläutert von ", "dessinées par ", "dessinée par ", "eröffnet und beschrieben von ",
                           "von Gymnasialdirector ", "Bijdrage van ", ", by ", " di ", "instruxit ", " scripsit ", "Bijdrage van ", ", étude par "]
