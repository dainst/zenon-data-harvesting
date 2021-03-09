import urllib.parse
import urllib.request
import json
import re
import itertools
import unidecode
import write_error_to_logfile
import find_existing_doublets
from weighted_levenshtein import dam_lev
import ssl
from nltk.corpus import stopwords
from find_existing_doublets import check_cosine_similarity
from langdetect import detect
from nltk.tokenize import RegexpTokenizer

ssl._create_default_https_context = ssl._create_unverified_context

rda_codes = {'rdacarrier': {'sg': 'audio cartridge', 'sb': 'audio belt', 'se': 'audio cylinder', 'sd': 'audio disc',
                            'si': 'sound track reel', 'sq': 'audio roll', 'sw': 'audio wire reel',
                            'ss': 'audiocassette', 'st': 'audiotape reel', 'sz': 'other', 'ck': 'computer card',
                            'cb': 'computer chip cartridge', 'cd': 'computer disc', 'ce': 'computer disc cartridge',
                            'ca': 'computer tape cartridge ', 'cf': 'computer tape cassette',
                            'ch': 'computer tape reel', 'cr': 'online resource', 'cz': 'other', 'ha': 'aperture card',
                            'he': 'microfiche', 'hf': 'microfiche cassette', 'hb': 'microfilm cartridge',
                            'hc': 'microfilm cassette', 'hd': 'microfilm reel', 'hj': 'microfilm roll',
                            'hh': 'microfilm slip', 'hg': 'microopaque', 'hz': 'other', 'pp': 'microscope slide',
                            'pz': 'other', 'mc': 'film cartridge', 'mf': 'film cassette', 'mr': 'film reel',
                            'mo': 'film roll', 'gd': 'filmslip', 'gf': 'filmstrip', 'gc': 'filmstrip cartridge',
                            'gt': 'overhead transparency', 'gs': 'slide', 'mz': 'other', 'eh': 'stereograph card',
                            'es': 'stereograph disc', 'ez': 'other', 'no': 'card', 'nb': 'sheet', 'nc': 'volume'},
             'rdacontent': {'crd': 'cartographic dataset', 'cri': 'cartographic image',
                            'crm': 'cartographic moving image', 'crt': 'cartographic tactile image',
                            'crn': 'cartographic tactile three-dimensional form',
                            'crf': 'cartographic three-dimensional form', 'cod': 'computer dataset',
                            'cop': 'computer program', 'ntv': 'notated movement', 'ntm': 'notated music',
                            'prm': 'performed music', 'snd': 'sounds', 'spw': 'spoken word', 'sti': 'still image',
                            'tci': 'tactile image', 'tcm': 'tactile notated music', 'tcn': 'tactile notated movement',
                            'tct': 'tactile text', 'tcf': 'tactile three-dimensional form', 'txt': 'text',
                            'tdf': 'three-dimensional form', 'tdm': 'three-dimensional moving image',
                            'tdi': 'two-dimensional moving image', 'xxx': 'other', 'zzz': 'unspecified'},
             'rdamedia': {'s': 'audio', 'c': 'computer', 'h': 'microform', 'p': 'microscopic', 'g': 'projected',
                          'e': 'stereographic', 'n': 'unmediated', 'v': 'video'}}


typewriter_list = [['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
                   ['q', 'w', 'e', 'r', 't', 'z', 'u', 'i', 'o', 'p', 'ü', '+'],
                   ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ö', 'ä', '#'],
                   ['y', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '-']]

stopwords_dict = {'de': stopwords.words('german'), 'en': stopwords.words('english'), 'fr': stopwords.words('french'),
                  'es': stopwords.words('spanish'), 'it': stopwords.words('italian'), 'nl': stopwords.words('dutch')}

unskippable_words = ['katalog', 'catalog', 'catalogue', 'catalogo', 'catalogus', 'cataloog', 'anhang', 'appendix', 'appendices', 'appendice', 'apendice']

stopwords_for_search_in_zenon = ['bd', 'band', 'vol', 'volume']


def swagger_find(search_title, search_authors, year, year_of_review, title, rejected_titles, lang, authors, all_results):
    try:
        page_nr = 0
        empty_page = False
        while not empty_page:
            page_nr += 1
            search_authors = search_authors.replace(" ", "+")
            if year:
                url = u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0%5B%5D=' + search_title + '&type0%5B%5D=Title&lookfor0%5B%5D=' + search_authors \
                      + '&type0%5B%5D=Author&lookfor0%5B%5D=&type0%5B%5D=year&bool0%5B%5D=AND&lookfor1%5B%5D=Rez.zu&type0%5B%5D=Title&bool1%5B%5D=NOT&illustration=-1&daterange%5B%5D=publishDate&publishDatefrom=' \
                      + str(int(year) - 1) + '&publishDateto=' + str(int(year) + 1) + '&page=' + str(page_nr)
            elif year_of_review:
                url = u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0%5B%5D=' + search_title + '&type0%5B%5D=Title&lookfor0%5B%5D=' + search_authors \
                      + '&type0%5B%5D=Author&lookfor0%5B%5D=&type0%5B%5D=year&bool0%5B%5D=AND&lookfor1%5B%5D=Rez.zu&type0%5B%5D=Title&bool1%5B%5D=NOT&illustration=-1&daterange%5B%5D=publishDate&publishDatefrom=&publishDateto=' \
                      + year_of_review + '&page=' + str(page_nr)
            else:
                url = u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0%5B%5D=' + search_title + '&type0%5B%5D=Title&lookfor0%5B%5D=' + search_authors \
                      + '&type0%5B%5D=Author&lookfor0%5B%5D=&type0%5B%5D=year&bool0%5B%5D=AND&lookfor1%5B%5D=Rez.zu&type0%5B%5D=Title&bool1%5B%5D=NOT&illustration=-1&daterange%5B%5D=publishDate&publishDatefrom=&publishDateto='\
                      + '&page=' + str(page_nr)

            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                response = response.read()
            response = response.decode('utf-8')
            json_response = json.loads(response)
            if 'records' not in json_response:
                empty_page = True
                continue
            for found_record in json_response['records']:
                if 'title' not in found_record:
                    continue
                title_found = found_record["title"]
                if found_record["id"] + title_found not in rejected_titles:
                    similarity = check_cosine_similarity(title, title_found, found_record, rejected_titles, lang)
                    right_author = False
                    if similarity:
                        if 'authors' in found_record:
                            found_authors = []
                            if 'primary' in found_record['authors']:
                                for primary_author in found_record['authors']['primary']:
                                    found_authors.append(primary_author.split(', ')[0])
                            if 'secondary' in found_record['authors']:
                                for secondary_author in found_record['authors']['secondary']:
                                    found_authors.append(secondary_author.split(', ')[0])
                            if 'corporate' in found_record['authors']:
                                for primary_author in found_record['authors']['secondary']:
                                    found_authors.append(primary_author.split(', ')[0])
                            if authors:
                                for found_author in [aut for found_author in found_authors for aut in found_author.split()]:
                                    if right_author:
                                        break
                                    if [dam_lev(unidecode.unidecode(found_author), unidecode.unidecode(splitted_author)) for x in authors for splitted_author in x.split()]:
                                        print({found_author + '+' + splitted_author: dam_lev(unidecode.unidecode(found_author), unidecode.unidecode(splitted_author)) for x in authors for splitted_author in x.split()})
                                        if min([dam_lev(unidecode.unidecode(found_author), unidecode.unidecode(splitted_author)) for x in authors for splitted_author in x.split()]) <= (len(found_author)/3):
                                            # Vorsicht vor impliziten Typkonvertierungen von Zahlen zu bool
                                            right_author = True
                            else:
                                if not found_authors:
                                    right_author = True
                            if right_author:
                                all_results.append(found_record['id'])
                            else:
                                rejected_titles.append(found_record["id"] + title_found)
        return all_results
    except Exception as e:
        write_error_to_logfile.write(e)


def find(review, year, default_lang):
    try:
        title = review['reviewed_title']
        authors = review['reviewed_authors'] + review['reviewed_editors']
        year_of_review = review['year_of_publication']
        all_results = []
        review_titles = []
        title = unidecode.unidecode(title)
        try:
            lang = detect(title)
        except Exception as e:
            lang = default_lang
        if lang not in stopwords_dict:
            lang = default_lang
        rejected_titles = []
        search_title = ""
        search_authors = ""
        word_nr = 0
        author_nr = 0
        for author in authors:
            author = unidecode.unidecode(author)
            if author_nr < 2 and ('ß' not in author):
                search_authors = search_authors + "+" + author
            author_nr += 1
        search_authors = search_authors.strip("+")
        for word in RegexpTokenizer(r'\w+').tokenize(title):
            if ((not any(stopword in word for stopword in stopwords_for_search_in_zenon)) and (len(word) > 2) and (
                    word not in stopwords_dict[lang]) and (re.findall(r'^\d{1,2}$', word) == []) and (
                    re.findall(r'^[IVXLCDM]*$', word) == [])):
                word = urllib.parse.quote(word, safe='')
                search_title = search_title + "+" + word
                word_nr += 1
        # Generierung eines bereinigten Suchtitels
        search_title = search_title.strip("+")
        if not search_title:
            return all_results, review_titles
        all_results = swagger_find(search_title, search_authors, year, year_of_review, title, rejected_titles, lang, authors, all_results)
            # Suche mit vollständigen Daten
        if len(all_results) == 0:
            search_authors = search_authors.split("+")[0]
            all_results = swagger_find(search_title, search_authors, year, year_of_review, title, rejected_titles, lang, authors, all_results)
            # Suche nur mit dem ersten Autoren
        if len(all_results) == 0:
            search_title = ""
            adjusted_title = title.split(".")[0].split(":")[0].split(".")[0]
            adjusted_title = adjusted_title.replace("...", " ")
            for word in RegexpTokenizer(r'\w+').tokenize(adjusted_title):
                if ((not any(stopword in word for stopword in stopwords_for_search_in_zenon)) and (
                        len(word) > 2) and (word not in stopwords_dict[lang]) and (
                        re.findall(r'^\d{1,2}$', word) == []) and (re.findall(r'^[IVXLCDM]*$', word) == [])):
                    word = urllib.parse.quote(word, safe='')
                    if '%' in word:
                        continue
                    search_title = search_title + "+" + word
            search_title = search_title.strip("+")
            if not search_title:
                return all_results, review_titles
            all_results = swagger_find(search_title, search_authors, year, year_of_review, title, rejected_titles, lang, authors, all_results)
            # Suche mit verkürztem Titel
        if len(all_results) == 0:
            search_authors = ""
            if not search_title:
                return all_results, review_titles
            all_results = swagger_find(search_title, search_authors, year, year_of_review, title, rejected_titles, lang, authors, all_results)
            # Suche ohne Autorennamen
        if len(all_results) == 0:
            if len(search_title.split('+')) > 5:
                for pair in itertools.combinations(search_title.split("+"), 2):
                    search_title_without_words = search_title
                    if len(all_results) > 0:
                        break
                    for word in pair:
                        search_title_without_words = search_title_without_words.replace(word, '').replace('++',
                                                                                                          '+').strip(
                            '+')
                    all_results = swagger_find(search_title_without_words, search_authors, year, year_of_review, title, rejected_titles, lang, authors, all_results)
            else:
                for word in search_title.split("+"):
                    search_title_without_words = search_title
                    if len(all_results) > 0:
                        break
                    search_title_without_words = search_title_without_words.replace(word, '').replace('++',
                                                                                                      '+').strip(
                        '+')
                    all_results = swagger_find(search_title_without_words, search_authors, year, year_of_review, title, rejected_titles, lang, authors, all_results)
            # Suche unter Ausschluss von einem oder zwei Suchbegriffen je nach Länge des Titels
        for i in range(len(all_results)):
            review_titles.append(find_existing_doublets.create_review_titles_for_review_search(review))
        return all_results, review_titles

    except Exception as e:
        write_error_to_logfile.write(e)


# Spracherkennung verbessern!
# Darum kümmern, dass bei mehreren reviews der Link auf die richtige Publikation gesetzt wird, nicht auf die erste!
# Namen von Autoren auch in nicht invertierter Form bei der Suche verwenden?