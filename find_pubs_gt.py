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
import csv
from nameparser import HumanName
import ssl
import find_sysnumbers_of_volumes

months_and_seasons = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'August', 'September',
                      'Oktober', 'November', 'Dezember', 'Frühling', 'Sommer', 'Herbst', 'Winter',
                      'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos',
                      'Eylül', 'Ekim', 'Kasım', 'Aralık', 'bahar', '', 'yaz', 'sonbahar', 'kış',
                      'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                      'September', 'October', 'November', 'December', 'Summer', 'Spring', 'Autumn', 'Winter', 'Jahrgang']
ssl._create_default_https_context = ssl._create_unverified_context

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
        # Längenvergleich der Titel sollte stattfinden!!!
        [title_list, found_title_list] = [a[:length] for a in [title_list, found_title_list]]
        title_list_count = [title_list.count(word) for word in title_list if (word not in stopwords_dict[lang])]
        found_title_list_count = [found_title_list.count(word) for word in title_list if (word not in stopwords_dict[lang])]
        # #print(title_list, found_title_list)
        # hier muss irgendwie iterative levensthein rein!!!
        # mehr Worte skippen und danach die Similarität und übriggebliebene Wortlänge vergleichen.
        if list(set(title_list_count)) == [0] or list(set(found_title_list_count)) == [0]:
            return 0, False
        else:
            similarity = 1 - spatial.distance.cosine(title_list_count, found_title_list_count)
            if similarity > 0.6:
                pass
            '''if (similarity <= 0.65) and (similarity >= 0.5):
                for word in title_list:
                    for found_word in found_title_list:
                        if (iterative_levenshtein(word, found_word)) < (len(word)/4) and iterative_levenshtein(word, found_word) > 0:
                            #print('levenshtein_title_test')
                            #print(word, found_word, iterative_levenshtein(word, found_word))
                            #print(title)
                            #print(found_title)'''
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
                            if word in unskippable_words and title_list.index(word) in [0, 1]:
                                #print(title_list)
                                return 0, False
                    else:
                        skipped_word_nr += 1
                        if word in unskippable_words and title_list.index(word) in [0, 1]:
                            #print(title_list)
                            return 0, False
                if skipped_word_nr >= (len(title_list) / 3):
                    return 0, False
                if matches_nr > mismatches_nr * 2:
                    if similarity > 0.79:
                        #print(title_list, found_title_list)
                        #print('similarity:', similarity)
                        return similarity, True
                    else:
                        #print(lang)
                        #print(title_list)
                        #print(found_title_list)
                        #print(similarity)
                        if found_title == found_record['title']:
                            if input("Handelt es sich tatsächlich um eine Dublette? ") == "":
                                return similarity, True
                            else:
                                rejected_titles.append(found_record["id"] + found_title)
        return 0, False
    except Exception as e:
        write_error_to_logfile.write(e)



def swagger_find(search_title, search_authors, year, title, rejected_titles, possible_host_items, lang, authors, additional_physical_form_entrys, all_results, all_sims, is_host_item = False):
    try:
        page_nr = 0
        empty_page = False
        while not empty_page:
            page_nr += 1
            search_authors = search_authors.replace(" ", "+")
            if year:
                url = u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0%5B%5D=' + search_title + '&type0%5B%5D=Title&lookfor0%5B%5D=' + search_authors \
                      + '&type0%5B%5D=Author&lookfor0%5B%5D=&type0%5B%5D=year&bool0%5B%5D=AND&illustration=-1&daterange%5B%5D=publishDate&publishDatefrom=' \
                      + str(int(year) - 1) + '&publishDateto=' + str(int(year) + 1) + '&page=' + str(page_nr)
            else:
                url = u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0%5B%5D=' + search_title + '&type0%5B%5D=Title&lookfor0%5B%5D=' + search_authors \
                      + '&type0%5B%5D=Author&bool0%5B%5D=AND&illustration=-1&daterange%5B%5D=publishDate&publishDatefrom=&publishDateto=' + '&page=' + str(page_nr)
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                response = response.read()
            response = response.decode('utf-8')
            json_response = json.loads(response)
            if 'records' not in json_response:
                empty_page = True
                continue
            for found_record in json_response['records']:
                if "title" not in found_record:
                    continue
                title_found = found_record["title"]
                if (found_record["id"] + title_found not in rejected_titles) and (found_record['id'] not in all_results) \
                        and (found_record['id'] not in [par['zenon_id'] for par in additional_physical_form_entrys]):
                    sim, similarity = check_cosine_similarity(title, title_found, found_record, rejected_titles, lang)
                    right_author = False
                    right_year = False
                    if similarity:
                        #print(found_record['id'])
                        try:
                            #print('title is similar')
                            webfile = urllib.request.urlopen(
                                "https://zenon.dainst.org/Record/" + found_record['id'] + "/Export?style=MARC")
                            new_reader = MARCReader(webfile)
                            for file in new_reader:
                                par = False
                                #print(found_record)
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
                                    #print('authors', authors)
                                    if authors:
                                        for found_author in [aut for found_author in found_authors for aut in found_author.split()]:
                                            if found_author in authors:
                                                #print('found in authors')
                                                right_author = True
                                            if right_author:
                                                break
                                            if [iterative_levenshtein(unidecode.unidecode(found_author), unidecode.unidecode(splitted_author)) for x in authors for splitted_author in x.split()]:
                                                #print([iterative_levenshtein(unidecode.unidecode(found_author), unidecode.unidecode(splitted_author)) for x in authors for splitted_author in x.split()])
                                                if min([iterative_levenshtein(unidecode.unidecode(found_author), unidecode.unidecode(splitted_author)) for x in authors for splitted_author in x.split()]) <= (len(found_author)/3):
                                                    # Vorsicht vor impliziten Typkonvertierungen von Zahlen zu bool
                                                    right_author = True
                                    else:
                                        if not found_authors:
                                            right_author = True
                                found_year = [min([int(year) for year in re.findall(r'\d{4}', field)]) for field in [field['c'] for field in file.get_fields('260', '264') if field['c']] if '©' not in field and re.findall(r'\d{4}', field)]
                                #print(found_year, year)
                                if found_year and year:
                                    if found_year[0] in [int(year)-1, int(year), int(year)+1]:
                                        right_year = True
                                if not found_year and not year:
                                    right_year = True
                                all_child_records = find_sysnumbers_of_volumes.find_sysnumbers(found_record['id'])
                                #print(all_child_records)
                                parent_webfile = urllib.request.urlopen(
                                    "https://zenon.dainst.org/Record/" + found_record['id'] + "/Export?style=MARC")
                                new_reader = MARCReader(parent_webfile)
                                record_type = ''
                                for file in new_reader:
                                    record_type = file.leader[7]
                                if right_author and right_year:
                                    if found_record['id'] not in all_results:
                                        all_results.append(found_record['id'])
                                        all_sims.append(sim)
                                elif is_host_item and year in all_child_records:
                                    all_results.append(all_child_records[year])
                                elif is_host_item and all_child_records:
                                    if found_record['id'] not in all_results:
                                        all_results.append(found_record['id'])
                                        all_sims.append(sim)
                                elif is_host_item and (record_type in ['s', 'm']):
                                    all_results.append(found_record['id'])

                        except Exception as e:
                            write_error_to_logfile.write(e)
            if all_results and additional_physical_form_entrys:
                break
        return all_sims, all_results, rejected_titles, additional_physical_form_entrys
    except Exception as e:
        write_error_to_logfile.write(e)


def find(title, authors, year, default_lang, possible_host_items, is_host_item = False):
    try:
        #print(possible_host_items)
        all_sims = []
        all_results = []
        title = unidecode.unidecode(title)
        try:
            lang = detect(title)
        except:
            lang = default_lang
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
            all_sims, all_results, rejected_titles, additional_physical_form_entrys = swagger_find(search_title, search_authors, year, title, rejected_titles, possible_host_items,
                                                                                         lang, authors, additional_physical_form_entrys, all_sims, all_results, is_host_item)
            # Suche mit vollständigen Daten
            if not all_results:
                all_results = []
            if len(all_results) == 0:
                search_authors = search_authors.split("+")[0]
                all_sims, all_results, rejected_titles, additional_physical_form_entrys = swagger_find(search_title, search_authors, year, title, rejected_titles,
                                                                                             possible_host_items,
                                                                                             lang, authors, additional_physical_form_entrys, all_sims, all_results, is_host_item)
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
                all_sims, all_results, rejected_titles, additional_physical_form_entrys = swagger_find(search_title, search_authors, year, title, rejected_titles,
                                                                                             possible_host_items,
                                                                                             lang, authors, additional_physical_form_entrys, all_sims, all_results, is_host_item)
                # Suche mit verkürztem Titel
            if len(all_results) == 0:
                search_authors = ""
                all_sims, all_results, rejected_titles, additional_physical_form_entrys = swagger_find(search_title, search_authors, year, title, rejected_titles,
                                                                                             possible_host_items,
                                                                                             lang, authors, additional_physical_form_entrys, all_sims, all_results, is_host_item)
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
                        all_sims, all_results, rejected_titles, additional_physical_form_entrys = swagger_find(search_title_without_words, search_authors, year, title,
                                                                                                     rejected_titles,
                                                                                                     possible_host_items, lang, authors, additional_physical_form_entrys, all_sims, all_results, is_host_item)
                else:
                    for word in search_title.split("+"):
                        search_title_without_words = search_title
                        if len(all_results) > 0:
                            break
                        search_title_without_words = search_title_without_words.replace(word, '').replace('++',
                                                                                                          '+').strip(
                            '+')
                        all_sims, all_results, rejected_titles, additional_physical_form_entrys = swagger_find(search_title_without_words, search_authors, year, title,
                                                                                                     rejected_titles,
                                                                                                     possible_host_items, lang, authors, additional_physical_form_entrys, all_sims, all_results, is_host_item)
                # Suche unter Ausschluss von einem oder zwei Suchbegriffen je nach Länge des Titels
        return all_results, additional_physical_form_entrys, all_sims
    except Exception as e:
        write_error_to_logfile.write(e)

def get_articles_zenon_ids():
    all_found_records = {}
    with open('gt_publications.csv', newline='') as csvfile:
        lkr_reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        row_nr = 0
        for row in lkr_reader:
            row_nr += 1
            #print('searching new record: row_nr', row_nr, row)
            authors_string = row[0]
            splitted = [a.strip() for author in authors_string.split(' and ') for auth in author.split(' und ') for aut in auth.split('; ') for a in aut.split(' – ')]
            splitted_by_komma = list(set([a if aut.count(' ') > aut.count(', ') else aut for aut in splitted for a in aut.split(', ')]))
            authors = list(set([HumanName(author).last for author in splitted_by_komma if HumanName(author).last]))
            title_string = row[1].replace('\n', ' ')
            pages = re.findall(r'[^\d]\d{1,3}[-|–]\d{1,3}', title_string)
            year_list = [int(year) for year in re.findall(r'\d{4}', title_string)]
            if row[2]:
                year = row[2]
            elif year_list:
                year = str(max(year_list))
            else:
                year = ''
            for item in pages:
                title_string = title_string.split(item)[0].strip().strip(',')
            if 'In: ' in title_string:
                title_string, host_item = title_string.split('In: ')[:2]
            if 'in: ' in title_string:
                title_string, host_item = title_string.split('in: ')[:2]
            title_string_splitted_list = title_string.split(',')
            if len(title_string_splitted_list[0].split()) < 2:
                title_string = ','.join(title_string_splitted_list[:2])
            else:
                title_string = title_string_splitted_list[0]
            all_resutls, adds, all_sims = find(title_string, authors, year, 'de', [])  # title, authors, year, default_lang, possible_host_items
            if all_resutls:
                #print('found matching record: ', all_resutls)
                all_found_records[str(row_nr)] = [all_resutls, all_sims]
            else:
                #print('no matching record found')
                # Suche nach host items:
                title_string = row[1].replace('\n', '')
                for string in pages:
                    title_string = title_string.replace(string, '').strip('.').strip().strip(',').strip().strip(':')
                host_item = ''
                if 'In: ' in title_string:
                    title_string, host_item = title_string.split('In: ')[:2]
                elif 'in: ' in title_string:
                    title_string, host_item = title_string.split('in: ')[:2]
                if host_item:
                    if re.findall(r'\([^\d]+?\)', host_item):
                        va, host_item = host_item.split(re.findall(r'\([^\d]+?\)', host_item)[0])
                        # #print(va)
                        host_item = host_item.strip(',').strip()
                        # #print(host_item)
                else:
                    splitted = title_string.rsplit(',', 1)
                    splitted.reverse()
                    for entry in splitted:
                        # #print(re.findall(r'\d', entry))
                        if len(re.findall(r'\d', entry)) > len(entry)/3:
                            splitted.reverse()
                            splitted = splitted[:-1]
                            title_string = ','.join(splitted)
                    title_string = title_string.strip(' pp.')
                    if len(title_string.rsplit(',')) < 3:
                        title_string = title_string.rsplit(',', 1)[-1].split('.')[-1]
                        for number in re.findall(r'\d', title_string):
                            title_string = title_string.rsplit(number, 1)[0]
                        host_item = title_string
                    if not host_item:

                        title_string = row[1].replace('\n', ' ')
                        for item in pages:
                            title_string = title_string.split(item)[0].strip().strip(',')
                        title_string = title_string.strip(' pp.').strip(',')
                        splitted = title_string.rsplit(',', 1)
                        splitted.reverse()
                        for entry in splitted:
                            # #print(re.findall(r'\d', entry))
                            if len(re.findall(r'\d', entry)) > len(entry)/3:
                                splitted.reverse()
                                splitted = splitted[:-1]
                                title_string = ','.join(splitted)

                        splitted = title_string.rsplit(',')
                        # #print(splitted)
                        if [word for word in months_and_seasons if word in splitted[-1] and word]:
                            splitted = splitted[:-1]
                            if [word for word in months_and_seasons if word in splitted[-1] and word]:
                                host_item = splitted[-2]
                            else:
                                host_item = splitted[-1]
                        else:
                            host_item = splitted[-1]
                if not host_item:
                    title_string = row[1].replace('\n', ' ')
                    for item in pages:
                        title_string = title_string.split(item)[0].strip().strip(',')
                    title_string = title_string.strip(' pp.').strip(',')
                    splitted = title_string.rsplit(',')
                    splitted.reverse()

                    for entry in splitted:
                        # #print(re.findall(r'\d', entry))
                        if len(re.findall(r'\d', entry)) > len(entry)/3:
                            title_string = title_string.replace(',' + entry, '')
                    host_item = title_string.rsplit(', ', 1)[-1].rsplit('. ')[-1]
                host_item = host_item.strip()
                #print('host item name:', host_item)
                all_resutls, adds, all_sims =  find(host_item, [], year, 'de', [], is_host_item=True)
                #print('host_item:', all_resutls)
    return all_found_records


def get_host_items_zenon_ids():
    with open('gt_publications.csv', newline='') as csvfile:
        lkr_reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        row_nr = 0
        for row in lkr_reader:
            row_nr += 1
            search_title_host_item = ''
            year = ''
            all_resutls, adds, all_sims = find(search_title_host_item, [], year, 'de', [])  # title, authors, year, default_lang, possible_host_items
            '''
            if [field['b'] for field in file.get_fields('995') if field['b'] and field['a'] == 'ANA']:
                if [field['b'] for field in file.get_fields('995') if field['b'] and field['a'] == 'ANA'][0] in possible_host_items:
                    right_host_item = True
                else:
                    try:
                        parent_webfile = urllib.request.urlopen(
                            "https://zenon.dainst.org/Record/" + file['995'][
                                'b'] + "/Export?style=MARC")
                        new_reader = MARCReader(parent_webfile)
                        for parent_file in new_reader:
                            if [field['b'] for field in parent_file.get_fields('995') if field['b'] and field['a'] == 'ANA']:
                                if [field['b'] for field in parent_file.get_fields('995') if field['b'] and field['a'] == 'ANA'][0] in possible_host_items:
                                    right_host_item = True
                    except:
                        #print('Das Host-Item von', found_record['id'], 'hat ein ungültiges Host-Item bzw. es gibt ein Problem mit der Weiterleitung.')
            if right_host_item is False:
                rejected_titles.append(found_record["id"] + title_found)
                continue'''


if __name__ == '__main__':
    get_articles_zenon_ids()

# dictionary mit gefundenen Publikationen abspeichern,
# jeweils die übergeordneten Publikationen suchen.
