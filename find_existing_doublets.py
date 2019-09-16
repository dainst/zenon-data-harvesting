import urllib.parse
import urllib.request
from langdetect import detect
from nltk.tokenize import RegexpTokenizer
import json
import re
import os
import sys
from nltk.corpus import stopwords
from scipy import spatial
import itertools
from pymarc import MARCReader
import math
import unidecode

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
        print('Error! Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e)))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


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
        print('Error! Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e)))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


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
                            if input("Handelt es sich tatsächlich um eine Dublette? ") == "":
                                return True
                            else:
                                rejected_titles.append(found_record["id"] + found_title)
        return False
    except Exception as e:
        print('Error! Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e)))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


def swagger_find(search_title, search_authors, year, title, rejected_titles, possible_host_items, lang, authors, additional_physical_form_entrys, publication_dict, all_results):
    try:
        search_authors = search_authors.replace(" ", "+")
        if year:
            url = u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0%5B%5D=' + search_title + '&type0%5B%5D=Title&lookfor0%5B%5D=' + search_authors + '&type0%5B%5D=Author&lookfor0%5B%5D=&type0%5B%5D=year&bool0%5B%5D=AND&illustration=-1&daterange%5B%5D=publishDate&publishDatefrom=' + str(
                int(year) - 1) + '&publishDateto=' + str(int(year) + 1)
        else:
            url = u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0%5B%5D=' + search_title + '&type0%5B%5D=Title&lookfor0%5B%5D=' + search_authors + '&type0%5B%5D=Author&bool0%5B%5D=AND&illustration=-1&daterange%5B%5D=publishDate&publishDatefrom=&publishDateto='
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            response = response.read()
        response = response.decode('utf-8')
        json_response = json.loads(response)
        resultcount = json_response["resultCount"]
        if resultcount > 0:
            for found_record in json_response["records"]:
                title_found = found_record["title"]
                if found_record["id"] + title_found not in rejected_titles:
                    similarity = check_cosine_similarity(title, title_found, found_record, rejected_titles, lang)
                    right_author = False
                    right_year = False
                    if similarity:
                        webfile = urllib.request.urlopen(
                            "https://zenon.dainst.org/Record/" + found_record['id'] + "/Export?style=MARC")
                        new_reader = MARCReader(webfile)
                        for file in new_reader:
                            # hier Möglichkeit für review einbauen? oder anderes Vorgehen?
                            if publication_dict['LDR_06_07'][1] == file.leader[7]:
                                par = False
                                if possible_host_items:
                                    right_host_item = False
                                    if file['995'] is not None:
                                        if file['995']['b'] is not None:
                                            if file['995']['b'] in possible_host_items:
                                                right_host_item = True
                                            else:
                                                parent_webfile = urllib.request.urlopen(
                                                    "https://zenon.dainst.org/Record/" + file['995'][
                                                        'b'] + "/Export?style=MARC")
                                                new_reader = MARCReader(parent_webfile)
                                                for parent_file in new_reader:
                                                    if parent_file['995'] is not None:
                                                        if parent_file['995']['b'] in possible_host_items:
                                                            right_host_item = True
                                    if right_host_item is False:
                                        rejected_titles.append(found_record["id"] + title_found)
                                        continue
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
                                            if [iterative_levenshtein(unidecode.unidecode(found_author), unidecode.unidecode(splitted_author)) for x in authors for splitted_author in x.split()]:
                                                if min([iterative_levenshtein(unidecode.unidecode(found_author), unidecode.unidecode(splitted_author)) for x in authors for splitted_author in x.split()]) <= (len(found_author)/3):
                                                    # Vorsicht vor impliziten Typkonvertierungen von Zahlen zu bool
                                                    right_author = True
                                    else:
                                        if not found_authors:
                                            right_author = True
                                found_year = [min([int(year) for year in re.findall(r'\d{4}', field)]) for field in [field['c'] for field in file.get_fields('260', '264') if field['c']] if '©' not in field and re.findall(r'\d{4}', field)]
                                if found_year and year:
                                    if found_year[0] in [int(year)-1, int(year), int(year)+1]:
                                        right_year = True
                                if not found_year and not year:
                                    right_year = True
                                if file['245']['c'] and publication_dict['title_dict']['responsibility_statement']:
                                    right_responsibility = check_cosine_similarity(file['245']['c'], publication_dict['title_dict']['responsibility_statement'], found_record, rejected_titles, lang)
                                elif publication_dict['title_dict']['responsibility_statement']:
                                    right_responsibility = False
                                else:
                                    right_responsibility = True
                                if right_author and right_responsibility and right_year:
                                    if found_record['id'] not in [entry['zenon_id'] for entry in additional_physical_form_entrys]:
                                        e_resource = False
                                        if file['337']:
                                            if (file['337']['b'] != publication_dict['rdamedia']) or (file['337']['a'] != rda_codes['rdamedia'][publication_dict['rdamedia']]):
                                                par = True
                                                if file['337']['b'] =='c' or file['337']['a'] == 'computer':
                                                    e_resource = True
                                        if file['338']:
                                            if (file['338']['b'] != publication_dict['rdacarrier']) or (file['338']['a'] != rda_codes['rdacarrier'][publication_dict['rdacarrier']]):
                                                par = True
                                                if file['338']['b'] =='cr' or file['338']['a'] == 'online resource':
                                                    e_resource = True
                                        if file['006']:
                                            if publication_dict['field_006'][0] != str(file['006'].data)[0]:
                                                par = True
                                                if str(file['006'].data)[0] == 'm':
                                                    e_resource = True
                                        if file['007']:
                                            if publication_dict['field_007'][0:2] != str(file['007'])[0:2]:
                                                par = True
                                                if str(file['007'].data)[0] == 'c':
                                                    e_resource = True
                                        if publication_dict['pdf_links'] or publication_dict['html_links'] or [link for link in publication_dict['other_links_with_public_note'] if 'online' in link['public_note']]:
                                            if file['856']:
                                                if 'online' in str(file['856']['z']).lower():
                                                    par = False
                                                else:
                                                    par = True
                                            else:
                                                par = True
                                        else:
                                            if file['856']:
                                                if 'online' in str(file['856']['z']).lower():
                                                    par = True
                                                    e_resource = True
                                        if publication_dict['rdamedia'] != 'c':
                                            if file['300']:
                                                if ('online' in str(file['300']['a']).lower()):
                                                    par = True
                                                    e_resource = True
                                            if file['533']:
                                                if ('online' in str(file['533']['a']).lower()):
                                                    par = True
                                                    e_resource = True
                                            if file['590']:
                                                if [str(field['a']).lower() for field in file.get_fields('590') if 'online' in str(field['a']) or 'ebook' in str(field['a'])]:
                                                    par = True
                                                    e_resource = True
                                        else:
                                            if file['300']:
                                                if 'online' in str(file['300']['a']).lower():
                                                    par = False
                                            if file['533']:
                                                if 'online' in str(file['533']['a']).lower():
                                                    par = False
                                            if file['590']:
                                                if [str(field['a']).lower() for field in file.get_fields('590') if 'online' in str(field['a'].lower()) or 'ebook' in str(field['a'].lower())]:
                                                    par = False
                                        if par:
                                            if e_resource:
                                                subfield_i = 'Online version'
                                            else:
                                                subfield_i = 'Print version'
                                            additional_physical_form_entrys.append({'zenon_id': found_record['id'],
                                                                                    'subfield_i': subfield_i})
                                            # print('par found:', found_record['id'], publication_dict['table_of_contents_link'])
                                        elif not par:
                                            all_results.append(found_record['id'])
                                            # print('doublet found:', found_record['id'], publication_dict['table_of_contents_link'])
                                        else:
                                            rejected_titles.append(found_record["id"] + title_found)
        return all_results
    except Exception as e:
        print('Error! Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e)))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


def find(title, authors, year, default_lang, possible_host_items, publication_dict):
    try:
        all_results = []
        title = unidecode.unidecode(title)
        lang = detect(title)
        if lang not in stopwords_dict:
            lang = default_lang
        rejected_titles = []
        additional_physical_form_entrys = []
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
            all_results = swagger_find(search_title, search_authors, year, title, rejected_titles, possible_host_items,
                                       lang, authors, additional_physical_form_entrys, publication_dict, all_results)
            # Suche mit vollständigen Daten
            if len(all_results) == 0:
                search_authors = search_authors.split("+")[0]
                all_results = swagger_find(search_title, search_authors, year, title, rejected_titles,
                                           possible_host_items,
                                           lang, authors, additional_physical_form_entrys, publication_dict, all_results)
                # Suche nur mit dem ersten Autoren
            if len(all_results) == 0:
                search_title = ""
                adjusted_title = title.split(":")[0].split(".")[0]
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
                all_results = swagger_find(search_title, search_authors, year, title, rejected_titles,
                                           possible_host_items,
                                           lang, authors, additional_physical_form_entrys, publication_dict, all_results)
                # Suche mit verkürztem Titel
            if len(all_results) == 0:
                search_authors = ""
                all_results = swagger_find(search_title, search_authors, year, title, rejected_titles,
                                           possible_host_items,
                                           lang, authors, additional_physical_form_entrys, publication_dict, all_results)
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
                        all_results = swagger_find(search_title_without_words, search_authors, year, title,
                                                   rejected_titles,
                                                   possible_host_items, lang, authors, additional_physical_form_entrys, publication_dict, all_results)
                else:
                    for word in search_title.split("+"):
                        search_title_without_words = search_title
                        if len(all_results) > 0:
                            break
                        search_title_without_words = search_title_without_words.replace(word, '').replace('++',
                                                                                                          '+').strip(
                            '+')
                        all_results = swagger_find(search_title_without_words, search_authors, year, title,
                                                   rejected_titles,
                                                   possible_host_items, lang, authors, additional_physical_form_entrys, publication_dict, all_results)
                # Suche unter Ausschluss von einem oder zwei Suchbegriffen je nach Länge des Titels
            return all_results, additional_physical_form_entrys
    except Exception as e:
        print('Error! Code: {c}, Message, {m}'.format(c=type(e).__name__, m=str(e)))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


# Spracherkennung verbessern!
