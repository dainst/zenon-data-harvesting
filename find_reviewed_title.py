import urllib.parse
import urllib.request
from langdetect import detect
from nltk.tokenize import RegexpTokenizer
import json
import re
from nltk.corpus import stopwords
from scipy import spatial
import itertools
from pymarc import MARCReader
import math
import unidecode
import write_error_to_logfile
import find_existing_doublets

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


def lower_list(input_list):
    output_list = [word.lower() for word in input_list]
    return output_list


def typewriter_distance(letter1, letter2):
    try:
        typewriter_position = [(typewriter_list.index(row), row.index(letter)) if (typewriter_list.index(row) != 2) else (
            typewriter_list.index(row), row.index(letter) + 0.5) for letter in [letter1, letter2]
            for row in typewriter_list if (letter in row)]
        try:
            distance = math.sqrt((abs(typewriter_position[0][0] - typewriter_position[1][0])) ** 2 + (
                abs(typewriter_position[0][1] - typewriter_position[1][1])) ** 2)
        except:
            distance = 1
        return distance
    except Exception as e:
        write_error_to_logfile.write(e)


def iterative_levenshtein(s, t):
    try:
        s, t = [string.lower() for string in [s, t]]
        rows = len(s) + 1
        cols = len(t) + 1
        deletes, inserts, substitutes = 1, 1, 1
        dist = [[0.0 for x in range(cols)] for x in range(rows)]
        for row in range(1, rows):
            dist[row][0] = row * deletes
        for col in range(1, cols):
            dist[0][col] = col * inserts
        for col in range(1, cols):
            for row in range(1, rows):
                dist[row][col] = min(dist[row - 1][col] + deletes,
                                     dist[row][col - 1] + inserts,
                                     dist[row - 1][col - 1] + typewriter_distance(s[row - 1], t[col - 1]))
        return dist[len(s)][len(t)]
    except Exception as e:
        write_error_to_logfile.write(e)


def check_cosine_similarity(title, found_title, found_record, rejected_titles, lang):
    try:
        found_title = unidecode.unidecode(found_title)
        title = unidecode.unidecode(title)
        title_list = RegexpTokenizer(r'\w+').tokenize(title)
        found_title_list = RegexpTokenizer(r'\w+').tokenize(found_title)
        [title_list, found_title_list] = [lower_list(a) for a in [title_list, found_title_list]]
        title_list = [word for word in title_list if
                      ((re.findall(r'^\d{1,2}$', word) == []) and (re.findall(r'^[ivxlcdm]*$', word) == []))]
        found_title_list = [word for word in found_title_list if
                            ((re.findall(r'^\d{1,2}$', word) == []) and (re.findall(r'^[ivxlcdm]*$', word) == []))]
        title_list = [word for word in title_list if (word not in stopwords_for_search_in_zenon)]
        found_title_list = [word for word in found_title_list if (word not in stopwords_for_search_in_zenon)]
        [title_list, found_title_list] = [lower_list(a) for a in [title_list, found_title_list]]
        title_list = [word for word in title_list if ((word not in stopwords_dict[lang]) and (len(word) > 2))]
        found_title_list = [word for word in found_title_list if
                            ((word not in stopwords_dict[lang]) and (len(word) > 2))]
        length = min(len(title_list), len(found_title_list))
        [title_list, found_title_list] = [a[:length] for a in [title_list, found_title_list]]
        title_list_count = [title_list.count(word) for word in title_list if (word not in stopwords_dict[lang])]
        found_title_list_count = [found_title_list.count(word) for word in title_list]
        # hier muss irgendwie iterative levensthein rein!!!
        if list(set(title_list_count)) == [0] or list(set(found_title_list_count)) == [0]:
            return False
        else:
            similarity = 1 - spatial.distance.cosine(title_list_count, found_title_list_count)
            if similarity > 0.65:
                skipped_word_nr = 0
                mismatches_nr = 0
                matches_nr = 0
                for word in title_list:
                    if word in found_title_list:
                        if any(index == found_title_list.index(word) for index in
                               [title_list.index(word) + 1 + skipped_word_nr, title_list.index(word) + skipped_word_nr,
                                title_list.index(word) - 1 + skipped_word_nr]):
                            matches_nr += 1
                        else:
                            mismatches_nr += 1
                            skipped_word_nr += 1
                            if word in unskippable_words:
                                return False
                    else:
                        skipped_word_nr += 1
                        if word in unskippable_words:
                            return False
                if skipped_word_nr >= (len(title_list) / 3):
                    return False
                if matches_nr > mismatches_nr * 2:
                    if similarity > 0.77:
                        return True
                    else:
                        print(lang)
                        print(title_list)
                        print(found_title_list)
                        print(similarity)
                        if found_title == found_record['title']:
                            if input("Handelt es sich tatsächlich um den rezensierten Titel? ") == "":
                                return True
                            else:
                                rejected_titles.append(found_record["id"] + found_title)
        return False
    except Exception as e:
        write_error_to_logfile.write(e)


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
                        webfile = urllib.request.urlopen(
                            "https://zenon.dainst.org/Record/" + found_record['id'] + "/Export?style=MARC")
                        new_reader = MARCReader(webfile)
                        for file in new_reader:
                            if file.leader[7] not in ['b', 'i', 's']:
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
                                            if min([iterative_levenshtein(unidecode.unidecode(found_author), unidecode.unidecode(splitted_author)) for x in authors for splitted_author in x.split()]) <= (len(found_author)/3):
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
        if word_nr >= 1:
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
                all_results = swagger_find(search_title, search_authors, year, year_of_review, title, rejected_titles, lang, authors, all_results)
                # Suche mit verkürztem Titel
            if len(all_results) == 0:
                search_authors = ""
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