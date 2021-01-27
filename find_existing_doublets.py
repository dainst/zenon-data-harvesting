import urllib.parse
import urllib.request
from langdetect import detect
from nltk.tokenize import RegexpTokenizer
import nltk
nltk.download('stopwords')
import json
import re
from nltk.corpus import stopwords
from scipy import spatial
import itertools
from pymarc import MARCReader
import math
import unidecode
import write_error_to_logfile
from weighted_levenshtein import dam_lev
import numpy as np
import ssl
import time
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


def typewriter_distance(letter1, letter2):
    try:
        typewriter_position = [(typewriter_list.index(row), row.index(letter)) if (typewriter_list.index(row) != 2) else (
            typewriter_list.index(row), row.index(letter) + 0.5) for letter in [letter1, letter2]
                               for row in typewriter_list if (letter in row)]
        try:
            distance = (1 + (math.sqrt((abs(typewriter_position[0][0] - typewriter_position[1][0])) ** 2 + (
                abs(typewriter_position[0][1] - typewriter_position[1][1])) ** 2))/10) / 1.5
        except:
            distance = 1
        return distance
    except Exception as e:
        write_error_to_logfile.write(e)


def get_matrices():
    transpose_costs = np.full((128, 128), 0.75, dtype=np.float64)
    substitute_costs = np.ones((128, 128), dtype=np.float64)  # make a 2D array of 1's
    for character in [chr(ordinal) for ordinal in [i for i in range(48, 58)] + [i for i in range(97, 123)]]:
        for second_character in [chr(ordinal) for ordinal in [i for i in range(48, 58)] + [i for i in range(97, 123)]]:
            substitute_costs[ord(character), ord(second_character)] = typewriter_distance(character, second_character)
            substitute_costs[ord(second_character), ord(character)] = typewriter_distance(character, second_character)
    return substitute_costs, transpose_costs


substitute_costs, transpose_costs = get_matrices()


def lower_list(input_list):
    output_list = [word.lower() for word in input_list]
    return output_list


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
        # Längenvergleich der Titel sollte stattfinden!!!
        [title_list, found_title_list] = [a[:length] for a in [title_list, found_title_list]]
        title_list_count = [title_list.count(word) for word in title_list if (word not in stopwords_dict[lang])]
        found_title_list_count = [found_title_list.count(word) for word in title_list if (word not in stopwords_dict[lang])]
        if list(set(title_list_count)) == [0] or list(set(found_title_list_count)) == [0]:
            return False
        else:
            similarity = 1 - spatial.distance.cosine(title_list_count, found_title_list_count)
            if similarity > 0.65:
                word_nr = 0
                skipped_word_nr = 0
                mismatches_nr = 0
                matches_nr = 0
                for word in title_list:
                    max_distance = len(word)/5 if (len(word) > 4) else 1
                    if word in found_title_list[(word_nr - 1) if word_nr > 0 else word_nr:word_nr + 2]:
                        if any(approximate_word_nr == found_title_list.index(word) for approximate_word_nr in
                               [word_nr + 1, word_nr, word_nr - 1]):
                            matches_nr += 1
                    elif any(dam_lev(word, found_word, substitute_costs=substitute_costs, transpose_costs=transpose_costs) <= max_distance for found_word in
                             [found_title_list[(word_nr - 1) if word_nr > 0 else word_nr], found_title_list[word_nr], found_title_list[(word_nr + 1) if word_nr + 1 < len(found_title_list) else word_nr]]):
                        matches_nr += 1
                    else:
                        mismatches_nr += 1
                        skipped_word_nr += 1
                        if word in unskippable_words and title_list.index(word) in [0, 1]:
                            print(title_list)
                            return False
                    word_nr += 1
                if skipped_word_nr >= math.ceil(len(title_list) / 4):
                    return False
                if matches_nr > mismatches_nr * 2:
                    if similarity > 0.77:
                        return True
        return False
    except Exception as e:
        write_error_to_logfile.write(e)


def create_review_titles_for_review_search(review_dict):
    possible_review_titles = []
    reviewed_title = review_dict['reviewed_title']
    reviewed_responsibles = review_dict['reviewed_authors'] + review_dict['reviewed_editors']
    if reviewed_responsibles:
        for person in reviewed_responsibles:
            possible_review_titles.append('[Rez.zu]: ' + person + ': ' + reviewed_title)
    if len(reviewed_responsibles) >= 2:
        for pair in itertools.combinations(reviewed_responsibles, 2):
            possible_review_titles.append('[Rez.zu]: ' + ', '.join(pair) + ': ' + reviewed_title)
        reviewed_responsibles.reverse()
        for pair in itertools.combinations(reviewed_responsibles, 2):
            possible_review_titles.append('[Rez.zu]: ' + ', '.join(pair) + ': ' + reviewed_title)
    else:
        possible_review_titles.append('[Rez.zu]: ' + reviewed_title)
    return possible_review_titles


def create_response_titles_for_response_search(review_list):
    possible_review_titles = []
    reviewed_title = review_list[0]['reviewed_title']
    reviewed_responsibles = review_list[0]['reviewed_authors'] + review_list[1]['reviewed_editors']
    if reviewed_responsibles:
        for person in reviewed_responsibles:
            possible_review_titles.append('[Response to]:[Rez.zu] :' + person + ': ' + reviewed_title)
    if len(reviewed_responsibles) >= 2:
        for pair in itertools.combinations(reviewed_responsibles, 2):
            possible_review_titles.append('[Response to]:[Rez.zu] :' + ', '.join(pair) + ': ' + reviewed_title)
        reviewed_responsibles.reverse()
        for pair in itertools.combinations(reviewed_responsibles, 2):
            possible_review_titles.append('[Response to]:[Rez.zu] :' + ', '.join(pair) + ': ' + reviewed_title)
    else:
        possible_review_titles.append('[Response to]:[Rez.zu]: ' + reviewed_title)
    return possible_review_titles


def swagger_find(search_title, year, title, rejected_titles, possible_host_items, lang, authors,
                 additional_physical_form_entrys, publication_dict, all_results):
    try:
        tic = time.perf_counter()
        year = year.replace('[', '').replace(']', '')
        page_nr = 0
        empty_page = False
        while not empty_page:
            page_nr += 1
            if len(search_title) == 0:
                print('skipped_no_search_title')
                break
            url = u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0%5B%5D=' + search_title + '&type0%5B%5D=Title&lookfor0%5B%5D=' \
                  '&type0%5B%5D=Author&lookfor0%5B%5D=&type0%5B%5D=year&bool0%5B%5D=AND&illustration=-1&page=' + str(page_nr)
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                response = response.read()
            response = response.decode('utf-8')
            json_response = json.loads(response)
            host_items_pars = []
            upper_host_items = [] # enthält die übergeordneten Aufnahmen der übergeordneten Aufnahmen für den neuen Record
            upper_host_items_pars = [] # enthält deren Parallele Manifestationen.
            for host_item in possible_host_items:
                if host_item:
                    host_item = host_item.zfill(9)
                    webfile = urllib.request.urlopen(
                        "https://zenon.dainst.org/Record/" + host_item + "/Export?style=MARC")
                    new_reader = MARCReader(webfile)
                    for file in new_reader:
                        for host_item_id in [field['w'] for field in file.get_fields('773') if field['w']]:
                            upper_host_items.append(host_item_id)
                        for par_item_id in [field['w'] for field in file.get_fields('776') if field['w']]:
                            host_items_pars.append(par_item_id)
            for upper_host_item in upper_host_items:
                if upper_host_item:
                    upper_host_item = upper_host_item.zfill(9)
                    webfile = urllib.request.urlopen(
                        "https://zenon.dainst.org/Record/" + upper_host_item + "/Export?style=MARC")
                    new_reader = MARCReader(webfile)
                    for file in new_reader:
                        for par_item_id in [field['w'].replace('(DE-2553)', '') for field in file.get_fields('776') if field['w']]:
                            upper_host_items_pars.append(par_item_id)
            if 'records' not in json_response:
                empty_page = True
                continue
            for found_record in json_response['records']:
                toc = time.perf_counter()
                if toc-tic > 120:
                    print('lasted_too_long:', url)
                    empty_page = True
                    break
                if "title" not in found_record:
                    continue
                title_found = found_record["title"]
                if found_record["id"] not in (rejected_titles + all_results) and (found_record['id'] not in [par['zenon_id'] for par in additional_physical_form_entrys]):
                    similarity = check_cosine_similarity(title, title_found, found_record, rejected_titles, lang)
                    right_author = False
                    right_year = False
                    if similarity:
                        try:
                            webfile = urllib.request.urlopen(
                                "https://zenon.dainst.org/Record/" + found_record['id'] + "/Export?style=MARC")
                            new_reader = MARCReader(webfile)
                            for file in new_reader:
                                par = False
                                found_authors = []
                                if 'authors' in found_record:
                                    if 'primary' in found_record['authors']:
                                        for primary_author in found_record['authors']['primary']:
                                            found_authors.append(primary_author.split(', ')[0])
                                            if ' ' in primary_author.split(', ')[0]:
                                                found_authors.append(primary_author.split(', ')[0].replace(' ', '-'))
                                    if 'secondary' in found_record['authors']:
                                        for secondary_author in found_record['authors']['secondary']:
                                            found_authors.append(secondary_author.split(', ')[0])
                                            if ' ' in secondary_author.split(', ')[0]:
                                                found_authors.append(secondary_author.split(', ')[0].replace(' ', '-'))
                                    if 'corporate' in found_record['authors']:
                                        for corporate_author in found_record['authors']['corporate']:
                                            found_authors.append(corporate_author.split(', ')[0])
                                            if ' ' in corporate_author.split(', ')[0]:
                                                found_authors.append(corporate_author.split(', ')[0].replace(' ', '-'))
                                    if authors:
                                        for found_author in [aut for found_author in found_authors for aut in found_author.split()]:
                                            if found_author in authors:
                                                right_author = True
                                            if right_author:
                                                break
                                            if [dam_lev(unidecode.unidecode(found_author), unidecode.unidecode(splitted_author), substitute_costs=substitute_costs, transpose_costs=transpose_costs) for x in authors for splitted_author in x.split()]:
                                                # print({found_author + '+' + splitted_author: dam_lev(unidecode.unidecode(found_author), unidecode.unidecode(splitted_author), substitute_costs=substitute_costs, transpose_costs=transpose_costs) for x in authors for splitted_author in x.split()})
                                                if min([dam_lev(unidecode.unidecode(found_author), unidecode.unidecode(splitted_author), substitute_costs=substitute_costs, transpose_costs=transpose_costs) for x in authors for splitted_author in x.split()]) <= (len(found_author)/3):
                                                    # Vorsicht vor impliziten Typkonvertierungen von Zahlen zu bool
                                                    right_author = True
                                else:
                                    right_author = True
                                found_year = [min([int(year) for year in re.findall(r'\d{4}', field)]) for field in [field['c'] for field in file.get_fields('260', '264') if field['c']] if '©' not in field and re.findall(r'\d{4}', field)]
                                if found_year and year:
                                    if found_year[0] in [int(year)-1, int(year), int(year)+1]:
                                        right_year = True
                                if not found_year and not year:
                                    right_year = True
                                [possible_host_items.remove(item) for item in possible_host_items if not item]
                                if possible_host_items:
                                    right_host_item = False
                                    print('found host items:', [field['w'].replace('(DE-2553)', '') for field in file.get_fields('773') if field['w']])
                                    if [field['w'].replace('(DE-2553)', '') for field in file.get_fields('773') if field['w']]:
                                        if any([field['w'].replace('(DE-2553)', '') in possible_host_items for field in file.get_fields('773') if field['w']]):
                                            right_host_item = True
                                        else:
                                            try:
                                                parent_id = file['773']['w'].replace('(DE-2553)', '').zfill(9)
                                                parent_webfile = urllib.request.urlopen(
                                                    "https://zenon.dainst.org/Record/" + parent_id + "/Export?style=MARC")
                                                new_reader = MARCReader(parent_webfile)
                                                # öffnet übergeordnete Aufnahme
                                                for parent_file in new_reader:
                                                    print('parent_file:', parent_file['001'])
                                                    print([field['w'].replace('(DE-2553)', '') for field in parent_file.get_fields('773') if field['w']])
                                                    if [field['w'].replace('(DE-2553)', '') for field in parent_file.get_fields('773') if field['w']]:
                                                        if any([field['w'].replace('(DE-2553)', '') in upper_host_items for field in parent_file.get_fields('773') if field['w']]):
                                                            right_host_item = True
                                                        elif any([field['w'].replace('(DE-2553)', '') in possible_host_items for field in parent_file.get_fields('776') if field['w']]):
                                                            right_host_item = True
                                                        elif parent_file['001'].data in host_items_pars:
                                                            right_host_item = True
                                                        else:
                                                            upper_parent_id = parent_file['773']['w'].replace('(DE-2553)', '').zfill(9)
                                                            upper_parent_webfile = urllib.request.urlopen(
                                                                "https://zenon.dainst.org/Record/" + upper_parent_id + "/Export?style=MARC")
                                                            new_reader = MARCReader(upper_parent_webfile)
                                                            for upper_parent_file in new_reader:
                                                                upper_parent_file_pars = [field['w'].replace('(DE-2553)', '') for field in upper_parent_file.get_fields('776') if field['w']]
                                                                print('upper_parent_file_pars', upper_parent_file_pars)
                                                                if any([upper_parent_file_par in upper_host_items_pars for upper_parent_file_par in upper_parent_file_pars]):
                                                                    right_host_item = True
                                            except:
                                                print('Das Host-Item von', found_record['id'], 'hat ein ungültiges Host-Item bzw. es gibt ein Problem mit der Weiterleitung.')
                                    if not right_host_item:
                                        rejected_titles.append(found_record["id"])
                                        continue

                                if right_author:
                                    if found_record['id'] not in [entry['zenon_id'] for entry in additional_physical_form_entrys]:
                                        e_resource = False
                                        if file['337']:
                                            if (file['337']['b'] != publication_dict['rdamedia']) or (file['337']['a'] != rda_codes['rdamedia'][publication_dict['rdamedia']]):
                                                par = True
                                                if file['337']['b'] == 'c' or file['337']['a'] == 'computer':
                                                    e_resource = True
                                        if file['338']:
                                            if (file['338']['b'] != publication_dict['rdacarrier']) or (file['338']['a'] != rda_codes['rdacarrier'][publication_dict['rdacarrier']]):
                                                par = True
                                                if file['338']['b'] == 'cr' or file['338']['a'] == 'online resource':
                                                    e_resource = True
                                        if file['006'] and publication_dict['field_006']:
                                            if publication_dict['field_006'][0] != str(file['006'].data)[0]:
                                                par = True
                                                if str(file['006'].data)[0] == 'm':
                                                    e_resource = True
                                        if file['007']:
                                            if publication_dict['field_007'][0] != str(file['007'].data)[0]:
                                                par = True
                                                if str(file['007'].data)[0] == 'c':
                                                    e_resource = True
                                        if publication_dict['pdf_links'] or publication_dict['html_links'] \
                                                or [link for link in publication_dict['other_links_with_public_note'] if 'online' in link['public_note']]:
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
                                            print('additional entry:', found_record['id'])
                                        elif right_year:
                                            if found_record['id'] not in all_results:
                                                all_results.append(found_record['id'])
                                                print('doublet:', found_record['id'])
                                        else:
                                            rejected_titles.append(found_record["id"] + title_found)
                        except Exception as e:
                            write_error_to_logfile.write(e)
                    else:
                        rejected_titles.append(found_record['id'])
            if all_results and additional_physical_form_entrys:
                break
        return all_results, rejected_titles, additional_physical_form_entrys
    except Exception as e:
        write_error_to_logfile.write(e)
        return all_results, rejected_titles, additional_physical_form_entrys


def find(authors, year, default_lang, possible_host_items, publication_dict):
    try:
        if publication_dict['review']:
            titles = create_review_titles_for_review_search(publication_dict['review_list'][0])
        elif publication_dict['response']:
            titles = create_response_titles_for_response_search(publication_dict['response_list'][0])
        else:
            titles = [publication_dict['title_dict']['main_title']]
        all_results = []
        rejected_titles = []
        additional_physical_form_entrys = []
        for title in titles:
            title = unidecode.unidecode(title)
            lang = detect(title)
            if lang not in stopwords_dict:
                lang = default_lang
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
            all_results, rejected_titles, additional_physical_form_entrys = swagger_find(search_title, year, title, rejected_titles,
                                       possible_host_items,
                                       lang, authors, additional_physical_form_entrys, publication_dict, all_results)
            # Suche mit verkürztem Titel
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
                        all_results, rejected_titles, additional_physical_form_entrys = swagger_find(search_title_without_words, year, title,
                                                   rejected_titles,
                                                   possible_host_items, lang, authors, additional_physical_form_entrys, publication_dict, all_results)
                else:
                    for word in search_title.split("+"):
                        search_title_without_words = search_title
                        if len(all_results) > 0:
                            break
                        search_title_without_words = search_title_without_words.replace(word, '').replace('++',
                                                                                                          '+').strip('+')
                        all_results, rejected_titles, additional_physical_form_entrys = swagger_find(search_title_without_words, year, title,
                                                   rejected_titles,
                                                   possible_host_items, lang, authors, additional_physical_form_entrys, publication_dict, all_results)
                # Suche unter Ausschluss von einem oder zwei Suchbegriffen je nach Länge des Titels
        return all_results, additional_physical_form_entrys
    except Exception as e:
        write_error_to_logfile.write(e)


# Spracherkennung verbessern!
# Behandlung bei der Suche nach Rezensionsdubletten UND rezensierten Titeln verbessern!!!
# hier noch Möglichkeiten für hidden filters einbauen?
# Problem: bei sehr kurzen "Haupttiteln" werden zu kurze Dublettentitel gefunden.
# Korrektur: aussortierte Worte zulassen, falls gar keine Worte für die Suche vorhanden sind.