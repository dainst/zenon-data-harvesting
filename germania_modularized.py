import urllib.parse
import urllib.request
from nameparser import HumanName
from bs4 import BeautifulSoup
import spacy
from langdetect import detect
import language_codes
import re
import json
import write_error_to_logfile
from harvest_records import harvest_records
from find_sysnumbers_of_volumes import find_sysnumbers
import gnd_request_for_cor

unresolved_titles = {
    "H. G. Bandi und J. Maringer, Kunst der Eiszeit. Levantekunst. Arktische Kunst": "H. G. Bandi und J. Maringer",
    "C. F. A. Schaeffer, Stratigraphie Comparée et Chronologie de l’Asie Occidentale (IIIe et IIe millénaires)": "C. F. A. Schaeffer",
    "G. Freund, Die Blattspitzen des Paläolithikums in Europa": "G. Freund",
    "Cl. F.-A. Schaeffer, Ugaritica II": "Cl. F.-A. Schaeffer",
    "Siegfried J. De Laet, Portorium. Etude sur l'organisation douanière chez  les Romains surtout à l'époque du Haut-Empire": "Siegfried J. De Laet",
    "K. H. Jacob-Friesen, Die Altsteinzeitfunde aus dem Leinetal bei Hannover": "K. H. Jacob-Friesen",
    "Dorin Popescu, Die frühe und mittlere Bronzezeit in Siebenbürgen": "Dorin Popescu",
    "Mozsolics Amália, A Kisapostagi Korabronzkori Urnateinető, Függelék: Méri István, A mészbetétágy elkészítésének módja a Kisapostagi edényeken": "Mozsolics Amália",
    "Thesaurus Antiquitatum Transsilvanicarum Teil 1. Praehistorica": None,
    "Janós Dombay, A Zengővárkonyi őskori telep és temető (The Prehistoric Settlement and Cemetery at Zengővárkony)": "Janós Dombay",
    "K. H. Jacob-Friesen, Einführung in Niedersachsens Urgeschichte. Darstellungen aus Niedersachsens Urgeschichte. Band 1": "K. H. Jacob-Friesen",
    "Gotlands Bildsteine. Band 1": None, "Oleh Kandyba, Schipenitz": "Oleh Kandyba",
    "Marg. Bachmann, Die Verbreitung der slavischen Siedlungen in Nordbayern": "Marg. Bachmann",
    "Eugen v. Frauenholz, Das Heerwesen der germanischen Frühzeit, des Frankenreiches und des ritterlichen Zeitalters": "Eugen v. Frauenholz",
    "R. Neuville - A. Rühlmann, LaPlace du Paleolithique Ancien dans le Quaternaire Marocain": "R. Neuville und A. Rühlmann",
    "Saint Catharine’s Hill, Winchester": None,
    "Miles Burkitt and V. Gordon Childe, A Chronological Table of Prehistory": "Miles Burkitt und V. Gordon Childe",
    "W. Vermeulen, Een romeinsch Grafveld op den Hunnerberg te Nymegen": "W. Vermeulen"}


nlp_dict = {'de': 'de_core_news_sm', 'en': 'en_core_web_sm', 'fr': 'fr_core_news_sm',
            'es': 'es_core_news_sm', 'it': 'it_core_news_sm', 'nl': 'nl_core_news_sm', 'xx': 'xx_ent_wiki_sm'}


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        volumes_sysnumbers = find_sysnumbers('000054792')
        basic_url = 'https://journals.ub.uni-heidelberg.de/index.php/germania/issue/archive/'
        empty_page = False
        page = 0
        cancelled = False
        while not empty_page and not cancelled:
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
            issues = journal_soup.find_all('a', class_='title')
            if not issues:
                empty_page = True
            for issue in issues:
                if cancelled:
                    break
                issue_information = issue.text
                publication_year = issue_information.strip().strip("Bd. ").split("(")[1].split(")")[0]
                if int(re.findall(r'\d{4}', publication_year)[0]) < 2015:
                    continue
                volume, volume_year = issue_information.strip().strip("Bd. ").split("(")[0].split(" ")
                current_item = int(publication_year + str(max([int(vol) for vol in re.findall(r'\d+', volume)])).zfill(3))
                print(current_item, last_item_harvested_in_last_session)
                if current_item > last_item_harvested_in_last_session:
                    if publication_year not in volumes_sysnumbers:
                        write_error_to_logfile.comment('Artikel von Germania konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr '
                                                       + publication_year + ' existiert.')
                        write_error_to_logfile.comment('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr ' + publication_year + '.')
                        break
                    issue_url = issue['href']
                    req = urllib.request.Request(issue_url, data, headers)
                    with urllib.request.urlopen(req) as response:
                        issue_page = response.read().decode('utf-8')
                    issue_soup = BeautifulSoup(issue_page, 'html.parser')
                    for article in issue_soup.find_all('div', class_='obj_article_summary'):
                        if not any(word in article.text for word in
                                   ["Titelei", "Inhalt", "Vorwort", "Titel", "Literatur", "Widmung", "Beilage",
                                    "Neuerscheinungen", "Besprechungen", "Hinweise für Publikationen", "Guidelines for Publications", "Recommandations aux auteurs"]):
                            article_url = article.find('div', class_='title').find('a')['href']
                            req = urllib.request.Request(article_url, data, headers)
                            with urllib.request.urlopen(req) as response:
                                article_page = response.read().decode('utf-8')
                            article_soup = BeautifulSoup(article_page, 'html.parser')
                            category = article_soup.find('li', class_="current").text.strip()
                            if category in ["Sonstiges", "Literatur"]:
                                continue
                            with open('publication_dict.json', 'r') as publication_dict_template:
                                publication_dict = json.load(publication_dict_template)
                            publication_dict['text_body_for_lang_detection'] = article_soup.find('meta', attrs={'name': 'DC.Description'})['content']
                            publication_dict['volume'] = volume
                            publication_dict['rdacontent'] = 'txt'
                            publication_dict['rdamedia'] = 'c'
                            publication_dict['rdacarrier'] = 'cr'
                            publication_dict['authors_list'] = [HumanName(author_tag['content']).last + ', ' + HumanName(author_tag['content']).first
                                                                if not gnd_request_for_cor.check_gnd_for_name(author_tag['content']) else author_tag['content']
                                                                for author_tag in article_soup.find_all('meta', attrs={'name': 'citation_author'})]
                            publication_dict['host_item']['name'] = 'Germania'
                            publication_dict['host_item']['sysnumber'] = volumes_sysnumbers[publication_year]
                            publication_dict['title_dict']['main_title'] = article_soup.find('meta', attrs={'name': 'citation_title'})['content']
                            publication_dict['publication_year'] = publication_year
                            if article_soup.find('meta', attrs={'name': 'citation_doi'}):
                                publication_dict['doi'] = article_soup.find('meta', attrs={'name': 'citation_doi'})['content']
                            publication_dict['abstract_link'] = article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']
                            if article_soup.find('meta', attrs={'name': 'citation_pdf_url'}):
                                publication_dict['pdf_links'].append(article_soup.find('meta', attrs={'name': 'citation_pdf_url'})['content'])
                            if article_soup.find('meta', attrs={'name': 'DC.Identifier.pageNumber'}):
                                publication_dict['pages'] = 'p. ' + article_soup.find('meta', attrs={'name': 'DC.Identifier.pageNumber'})['content']
                            publication_dict['rdacarrier'] = 'cr'
                            publication_dict['rdamedia'] = 'c'
                            publication_dict['rdacontent'] = 'txt'
                            publication_dict['LDR_06_07'] = 'ab'
                            publication_dict['field_006'] = 'm     o  d |      '
                            if int(publication_dict['publication_year']) > 2013:
                                publication_dict['field_007'] = 'cr uuu   uu|uu'
                                publication_dict['default_language'] = language_codes.resolve(article_soup.find('meta', attrs={'name': 'DC.Language'})['content'])
                                publication_dict['do_detect_lang'] = False
                            else:
                                publication_dict['field_007'] = 'cr uuu   uuauu'
                                publication_dict['retro_digitization_info'] = \
                                    {'place_of_publisher': 'Heidelberg', 'publisher': 'Heidelberg UB',
                                     'date_published_online': article_soup.find('div', class_='published').find('div', class_='value').text.strip()}
                                publication_dict['default_language'] = language_codes.resolve(article_soup.find('meta', attrs={'name': 'DC.Language'})['content'])
                            publication_dict['field_008_18-34'] = 'gr poo||||||   b|'
                            publication_dict['fields_590'] = ['arom', '2020xhnxgerm', 'Online publication', 'daiauf8']
                            publication_dict['original_cataloging_agency'] = 'DE-16'
                            publication_dict['publication_etc_statement']['publication'] = {'place': 'Heidelberg',
                                                                                            'responsible': 'Propylaeum',
                                                                                            'country_code': 'gw '}
                            publication_dict['table_of_contents_link'] = issue_url
                            publication_dict['volume_year'] = volume_year
                            publication_dict['copyright_year'] = re.findall(r'\d{4}', article_soup.find('meta', attrs={'name': 'DC.Rights'})['content'])[0]
                            if article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']:
                                publication_dict['abstract_link'] = article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']
                            if category == "Rezensionen / Reviews / Comptes rendus":
                                title = publication_dict['title_dict']['main_title'].strip()
                                titles = [title]
                                if ' / ' in title:
                                    parts = title.split(' / ')
                                    start_of_next_part = 0
                                    for part in parts:
                                        if len(part) > 30 and title not in ['Eva Alram-Stern / Angelika Dousougli-Zachos, Die deutschen Ausgrabungen 1941 auf der Visviki-Magula / Velestino. Die neolithischen Befunde und Funde',
                                                                            'Niedersächsisches Institut für historische Küstenforschung (ed.), Marschenratskolloquium 2012. Flint von Helgoland – Die Nutzung einer einzigartigen Rohstoffquelle an der Nordseeküste / Marshland Council Colloquium 2012. Flint from Heligoland – the Exploitation of a Unique Source of Raw-Material on the North Sea Coast, 26.–28. April 2012']:
                                            titles = []
                                            if parts.index(part) != -1:
                                                titles.append(' / '.join(parts[start_of_next_part:parts.index(part)+1]))
                                                start_of_next_part = parts.index(part) + 1
                                            else:
                                                titles.append(' / '.join(parts[start_of_next_part:parts.index(part)+1]))
                                for title in titles:
                                    persons = []
                                    rev_authors = []
                                    rev_editors = []
                                    year_of_publication = ''
                                    last_person = ''
                                    editorship = False
                                    publication_dict['review'] = True
                                    if ' / ' in title:
                                        persons = [HumanName(person).last + ', ' + HumanName(person).first if not gnd_request_for_cor.check_gnd_for_name(person) else person
                                                   for person in title.split(' / ', title.count(' / '))[:-1]]
                                        title = title.split(' / ', title.count(' / '))[-1]
                                    for editorship_word in [" (Red.)", " (Hrsg.)", " (ed.)", " (eds)"]:
                                        if editorship_word in title:
                                            editorship = True
                                            title = title.replace(editorship_word, '')
                                    title = title.strip()
                                    lang = detect(title)
                                    if lang in ["de", "en", "fr", "it", "es", "nl"]:
                                        nlp = spacy.load(nlp_dict[lang])
                                        tagged_sentence = nlp(title)
                                        propn = False
                                        punct = False
                                        for word in tagged_sentence:
                                            if propn and word.text == "und":
                                                continue
                                            if punct:
                                                break
                                            if word.pos_ not in ["PUNCT", "PROPN"]:
                                                break
                                            if word.pos_ == "PUNCT" and propn and word.text != "-":
                                                punct = True
                                                if len(title.split(word.text)[0].split()) > 1:
                                                    last_person = title.split(word.text)[0]
                                            if word.pos_ == "PROPN":
                                                propn = True
                                            else:
                                                propn = False
                                        if not last_person:
                                            for ent in tagged_sentence.ents:
                                                if ent.label_ == "PER":
                                                    if title.startswith(ent.text):
                                                        if len(ent.text.split()) > 1:
                                                            last_person = ent.text
                                                break
                                    else:
                                        nlp = spacy.load(nlp_dict['xx'])
                                        tagged_sentence = nlp(title)
                                        for ent in tagged_sentence.ents:
                                            if ent.label_ == "PER":
                                                if title.startswith(ent.text):
                                                    if len(ent.text.split()) > 1:
                                                        last_person = ent.text
                                                break

                                    if last_person:
                                        title = title.replace(last_person + ", ", "")
                                        persons.append(HumanName(last_person).last + ', ' + HumanName(last_person).first if not gnd_request_for_cor.check_gnd_for_name(last_person) else last_person)
                                        if editorship:
                                            rev_editors = persons
                                        else:
                                            rev_authors = persons
                                    if len(publication_dict['text_body_for_lang_detection']) > 35:
                                        year_of_publication = str(max([int(year) for year in re.findall(r'[^\d-](\d{4})[^\d-]', publication_dict['text_body_for_lang_detection'])]))
                                    publication_dict['review_list'].append({'reviewed_title': title,
                                                                            'reviewed_authors': rev_authors,
                                                                            'reviewed_editors': rev_editors,
                                                                            'year_of_publication': year_of_publication,
                                                                            })
                            publication_dicts.append(publication_dict)
                            items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Germania geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'germania', 'Germania', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/germania/', 'germania', 'Germania', create_publication_dicts)


# Lücke von 1960 bis 1985? > erst beim Hinzufügen der Links von Bedeutung.


'''publishers = {'1904': ['Frankfurt am Main', 'Baer'], '1921': ['Bamberg', 'Buchner'],
                                        '1932': ['Berlin', 'de Gruyter'], '1976': ['Mainz', 'von Zabern'],
                                        '2011': ['Darmstadt', 'von Zabern'],
                                        '2013': ['Frankfurt am Main', 'Henrich Editionen']}'''
