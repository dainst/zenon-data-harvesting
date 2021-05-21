from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
import nltk
import re
import spacy
from langdetect import detect
import urllib
from urllib import request, parse
import json
import unicodedata
import sys, os
import copy
import math
from statistics import mean, median, stdev
from geopandas import GeoSeries
from shapely.geometry import Polygon, Point

def get_distance_of_coordinates(coord_1, coord_2):
    R = 6373.0
    dlon = math.radians(coord_1[0]) - math.radians(coord_2[0])
    dlat = math.radians(coord_1[1]) - math.radians(coord_2[1])
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(coord_2[1])) * math.cos(math.radians(coord_1[1])) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

efb_gazetteer_data={}

def remove_parentheses(string):
    remove_parentheses = re.compile(".*?\((.*?)\)")
    result = re.findall(remove_parentheses, string)
    for item in result:
        string=string.replace("("+item+")", "")
    return string

#import urllib.parse, urllib.request
stemmer=nltk.stem.cistem.Cistem(case_insensitive=False)
nlp_de = spacy.load('de_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')
nlp_fr = spacy.load('fr_core_news_sm')
nlp_es = spacy.load('es_core_news_sm')
nlp_it = spacy.load('it_core_news_sm')
nlp_nl = spacy.load('nl_core_news_sm')
nlp_xx = spacy.load('xx_ent_wiki_sm')
with open('frequent_words.json', 'r') as frequent_words_file:
    frequent_words_dict=json.load(frequent_words_file)
stopwords_de=stopwords.words('german')
stopwords_en=stopwords.words('english')
stopwords_fr=stopwords.words('french')
stopwords_es=stopwords.words('spanish')
stopwords_it=stopwords.words('italian')
stopwords_nl=stopwords.words('dutch')

def remove_accents(token):
    nfkd_form = unicodedata.normalize('NFKD', token)
    token_without_accents = nfkd_form.encode('ASCII', 'ignore').decode('ascii')
    return token_without_accents

def check_similarity_and_create_hierarchy(possible_loc, possible_loc_before_parsing, result, ids, locs):
    try:
        if result['@id'] not in ids:
            coordinates = None
            if 'prefLocation' in result:
                if 'coordinates' in result['prefLocation']:
                    coordinates=result['prefLocation']['coordinates']
                    point = Point(coordinates)
                    coordinates = GeoSeries(point)
                elif 'shape' in result['prefLocation']:
                    coordinates=result['prefLocation']['shape']
                    liste = copy.deepcopy(coordinates)
                    while isinstance(liste[0], list):
                        if isinstance(liste[0][0], list) is not True:
                            break
                        liste=liste[0]
                    coordinates = liste
                    coordinates = [tuple(item) for item in coordinates]
                    polygon = Polygon(coordinates)
                    polygon = GeoSeries(polygon)
                    centroid = polygon.centroid
                    coordinates=GeoSeries(centroid)
            locs['loc'+result['@id'].split("/")[-1]]=possible_loc
            all_ancestors=[]
            all_ancestors_for_comparing=[]
            if 'parent' in result:
                id_of_ancestor=result['parent']
                all_ancestors_for_comparing.append(id_of_ancestor)
                all_ancestors.append(id_of_ancestor)
                while id_of_ancestor!="https://gazetteer.dainst.org/place/2042600":
                    search_url = "https://gazetteer.dainst.org/doc/"+id_of_ancestor.split('/')[-1]+".json"
                    req = urllib.request.Request(search_url)
                    with urllib.request.urlopen(req) as response:
                        json_response=response.read()
                    json_response=json_response.decode('utf-8')
                    json_response=json.loads(json_response)
                    id_of_ancestor=json_response['parent']
                    if coordinates is None:
                        if 'prefLocation' in json_response:
                            if 'coordinates' in json_response['prefLocation']:
                                coordinates=[tuple(json_response['prefLocation']['coordinates'])]
                                point = Point(coordinates)
                                coordinates = GeoSeries(point)
                            elif 'shape' in json_response['prefLocation']:
                                coordinates=json_response['prefLocation']['shape']
                                liste = copy.deepcopy(coordinates)
                                while isinstance(liste[0], list):
                                    if isinstance(liste[0][0], list) is not True:
                                        break
                                    liste=liste[0]
                                coordinates = liste
                                coordinates = [tuple(item) for item in coordinates]
                                polygon = Polygon(coordinates)
                                polygon = GeoSeries(polygon)
                                centroid = polygon.centroid
                                coordinates=GeoSeries(centroid)
                    all_ancestors.append(id_of_ancestor)
                    all_ancestors_for_comparing.append(id_of_ancestor)
                if 'ancestors' in result:
                    if all_ancestors_for_comparing[1:]!=result['ancestors']:
                        #print('Fehlerhafte Hierachie:', result['@id'])
                        #print('In den Daten:', result['ancestors'])
                        #print('Ermittelt:', all_ancestors_for_comparing)
                if ('ancestors' not in result) and (result['parent']!="https://gazetteer.dainst.org/place/2042600"):
                    #print(result['@id'], 'has no ancestors')
            else:
                #print(result['@id'], 'has no parent')
            if coordinates is None:
                #print('keine Koordinaten gefunden.', result['@id'])
            ids[result['@id']]={'count':str(text_to_process.count(possible_loc_before_parsing)), 'possible_loc':possible_loc_before_parsing, 'coordinates':coordinates, 'ancestors':all_ancestors}
        return ids, locs
    except Exception as e:
        #print('Error! Code: {c}, Message, {m}'.format(c = type(e).__name__, m = str(e)))
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #print(exc_type, fname, exc_tb.tb_lineno)

def check_locs(list_of_possible_locs, ids, locs):
    for possible_loc in list_of_possible_locs:
        possible_loc_before_parsing=possible_loc
        possible_loc=urllib.parse.quote(possible_loc, safe='').replace('%2F', '%20').replace('%21', '%20').replace('%29', '%20').replace('%28', '%20').replace('%25', '%20')
        search_url = "https://gazetteer.dainst.org/search.json?q="+possible_loc+"&offset=0&limit=150"
        req = urllib.request.Request(search_url)
        try:
            with urllib.request.urlopen(req) as response:
                json_response=response.read()
            json_response=json_response.decode('utf-8')
            json_response=json.loads(json_response)
            if 0<json_response['total']<100:
                for result in json_response['result']:
                    if remove_accents(remove_parentheses(result['prefName']['title'])).split(',')[0].split('/')[0].strip()==remove_accents(possible_loc_before_parsing):
                        ids, locs = check_similarity_and_create_hierarchy(possible_loc, possible_loc_before_parsing, result, ids, locs)
                    else:
                        if 'names' in result.keys():
                            for name in result['names']:
                                if remove_accents(remove_parentheses(name['title']).split(',')[0].split('/')[0].strip())==remove_accents(possible_loc_before_parsing):
                                    ids, locs = check_similarity_and_create_hierarchy(possible_loc, possible_loc_before_parsing, result, ids, locs)
                                    break
            elif json_response['total']==0:
                for part_of_possible_loc in possible_loc.split():
                    possible_loc_before_parsing=part_of_possible_loc
                    part_of_possible_loc=urllib.parse.quote(part_of_possible_loc, safe='').replace('%2F', '%20').replace('%21', '%20').replace('%29', '%20').replace('%28', '%20').replace('%25', '%20')
                    search_url = "https://gazetteer.dainst.org/search.json?q="+part_of_possible_loc+"&offset=0&limit=150"
                    req = urllib.request.Request(search_url)
                    with urllib.request.urlopen(req) as response:
                        json_response=response.read()
                    json_response=json_response.decode('utf-8')
                    json_response=json.loads(json_response)
                    if 0<json_response['total']:
                        for result in json_response['result']:
                            if remove_accents(remove_parentheses(result['prefName']['title'])).split(',')[0].split('/')[0].strip()==remove_accents(possible_loc_before_parsing):
                                ids, locs = check_similarity_and_create_hierarchy(possible_loc, possible_loc_before_parsing, result, ids, locs)
                            else:
                                if 'names' in result.keys():
                                    for name in result['names']:
                                        if remove_accents(remove_parentheses(name['title']).split(',')[0].split('/')[0].strip())==remove_accents(possible_loc_before_parsing):
                                            ids, locs = check_similarity_and_create_hierarchy(possible_loc, possible_loc_before_parsing, result, ids, locs)
                                            break

        except Exception as e:
            #print(search_url)
            #print('Error! Code: {c}, Message, {m}'.format(c = type(e).__name__, m = str(e)))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            #print(exc_type, fname, exc_tb.tb_lineno)
        #if found_items>1:
            ##print(found_items, search_url)
    return locs, ids

xml=open('hierarchy.rdf', 'r')
soup=BeautifulSoup(xml, 'xml')
subjects=soup.find_all('rdf:Description')
subject_dict={}
#Wikipedia überprüfen, ob der Ortsname 1. eindeutig vergeben ist und Koordinaten vorhanden sind.
#for subject in subjects:
    #if subject.find('skos:narrower')!=None:
        ##print(subject)
        #xml erstellen, das hierarchische Verhältnisse abbildet!!!
            #translator= Translator(to_lang="en", from_lang="de")
            #stemmed_subject_eng=stemmer.stem(RegexpTokenizer(r'\w+').tokenize(subject.find('skos:prefLabel').text)[0])

df={}
tf_dict={}
file_nr=0
#for file in os.listdir("eperiodica_text_files"):
for file in os.listdir('efb_text_files'):
    #print(file)
    possible_locs=[]
    locs={}
    ids={}
    if file_nr>1:
        break
    file_nr+=1
    ##print(file)
    tf_dict[file]={}
    text_to_process=(open('efb_text_files/'+file, 'r')).read()
    text_to_process=text_to_process.replace("-\n", "")
    text_to_process=text_to_process.replace("\n", " ")
    remove_parentheses(text_to_process)
    try:
        lang=detect(text_to_process)
    except:
        lang="de"
    text_length=len(RegexpTokenizer(r'\w+').tokenize(text_to_process))
    nlp=None
    nouns=[]
    if lang=="de":
        nlp=nlp_de
    elif lang=="en":
        nlp=nlp_en
    elif lang=="fr":
        nlp=nlp_fr
    elif lang=="it":
        nlp=nlp_it
    elif lang=="es":
        nlp=nlp_es
    elif lang=="nl":
        nlp=nlp_nl
    else:
        lang='de'
        nlp=nlp_de
    sentences=nltk.sent_tokenize(text_to_process)
    no_char=False
    for sentence in sentences:
        if len(sentence.split())>=4:
            tagged_sentence=nlp(sentence)
            for token in tagged_sentence:
                if token.pos_=="NOUN":
                    no_char=False
                    for token_text in token.text.split("-"):
                        token_text=token_text.split("/")[0]
                        #if token.text not in possible_locs:
                            #possible_locs.append(token_text)
                        character_nr=0
                        for character in token_text:
                            if (((64<ord(character)<91) or (191<ord(character)<222)) and character_nr!=0):
                                token_text=token_text.split(character)[0]
                            if not ((191<ord(character)<609) or (64<ord(character)<91) or (96<ord(character)<123)):
                                no_char=True
                            character_nr+=1
                        if len(token_text)>=3:
                            if no_char==True:
                                break
                            nouns.append(token_text)
    nouns_dict={}
    for noun in nouns:
        if noun not in nouns_dict:
            nouns_dict[noun]=nouns.count(noun)
    ##print(sorted(nouns_dict.items(), key=lambda x:x[1], reverse=True))
    lemmata ={}
    doc = nlp(text_to_process)
    for token in doc:
        lemmata[token]=token.lemma
    for ent in doc.ents:
        if ent.label_ in ["LOC", "GPE"]:
            TITLE = ent.text
            if TITLE not in possible_locs:
                possible_locs.append(TITLE)
                if TITLE in lemmata.keys():
                    possible_locs.append(lemmata[TITLE])
            for part_of_title in TITLE.split("-"):
                if part_of_title not in possible_locs:
                    possible_locs.append(part_of_title)
                    if part_of_title in lemmata.keys():
                        possible_locs.append(lemmata[part_of_title])
                    possible_locs.append(part_of_title)
    possible_locs = list(dict.fromkeys(possible_locs))
    possible_locs = [loc for loc in possible_locs if len(loc)>=2]
    locs, ids = check_locs(possible_locs, ids, locs)
    ids_sorted_by_possible_locs = {}
    for item in ids:
        if ids[item]['possible_loc'] not in ids_sorted_by_possible_locs:
            ids_sorted_by_possible_locs[ids[item]['possible_loc']]={}
        ids_sorted_by_possible_locs[ids[item]['possible_loc']][item] = ids[item]
    new_ids = {}
    all_points_median_and_stdev = {}
    for item in ids_sorted_by_possible_locs:
        all_points = [(float(ids_sorted_by_possible_locs[item][loc]['coordinates'].apply(lambda p: p.y)), float(ids_sorted_by_possible_locs[item][loc]['coordinates'].apply(lambda p: p.x))) for loc in ids_sorted_by_possible_locs[item] if ids_sorted_by_possible_locs[item][loc]['coordinates'] is not None]
        try:
            median_x = median([coord[0] for coord in all_points])
            median_y = median([coord[1] for coord in all_points])
            median_tuple = (median_x, median_y)
        except:
            median_x = mean([coord[0] for coord in all_points])
            median_y = mean([coord[1] for coord in all_points])
            median_tuple = (median_x, median_y)
        all_points_median_and_stdev[item]=median_tuple
    try:
        median_x = median([all_points_median_and_stdev[item][0] for item in all_points_median_and_stdev])
        median_y = median([all_points_median_and_stdev[item][1] for item in all_points_median_and_stdev])
        median_tuple = (median_x, median_y)
    except:
        median_x = mean([all_points_median_and_stdev[item][0] for item in all_points_median_and_stdev])
        median_y = mean([all_points_median_and_stdev[item][1] for item in all_points_median_and_stdev])
        median_tuple = (median_x, median_y)
    #print(median_tuple)
    [#print(item, get_distance_of_coordinates(all_points_median_and_stdev[item], median_tuple)) for item in all_points_median_and_stdev]
    dist = mean([get_distance_of_coordinates(all_points_median_and_stdev[item], median_tuple) for item in all_points_median_and_stdev])
    #print(dist)
    #hier jetzt aus den einzelnen Items alle rausnehmen, die zu weit entfernt sind, dann wieder mitteln, nochmal rausnehmen, dann alle items rausnehmen, die zu weit weg sind.


    #hier jetzt noch tf-idf-Ranking reinbringen!
    for item in ids_sorted_by_possible_locs:
        new_ids=ids_sorted_by_possible_locs[item]
        loops=0
        while len(new_ids)>1:
            if loops>=5:
                break
            loops+=1
            items_to_delete=[]
            for match in ids_sorted_by_possible_locs[item]:
                for other_match in ids_sorted_by_possible_locs[item]:
                    if match in ids_sorted_by_possible_locs[item][other_match]['ancestors']:
                        items_to_delete.append(other_match)
            for to_delete in items_to_delete:
                if to_delete in new_ids:
                    del new_ids[to_delete]
        if len(new_ids)>2:
            all_points = [(float(new_ids[loc]['coordinates'].apply(lambda p: p.x)), float(new_ids[loc]['coordinates'].apply(lambda p: p.y))) for loc in new_ids if new_ids[loc]['coordinates'] is not None]
            try:
                median_x = median([coord[0] for coord in all_points])
                median_y = median([coord[1] for coord in all_points])
                median_tuple = (median_x, median_y)
            except:
                median_x = mean([coord[0] for coord in all_points])
                median_y = mean([coord[1] for coord in all_points])
                median_tuple = (median_x, median_y)
            stdev_x = stdev([coord[0] for coord in all_points], median_x)
            stdev_y = stdev([coord[1] for coord in all_points], median_y)
            for loc in new_ids:
                if new_ids[loc]['coordinates'] is not None:
                    point = (float(new_ids[loc]['coordinates'].apply(lambda p: p.x)), float(ids_sorted_by_possible_locs[item][loc]['coordinates'].apply(lambda p: p.y)))
                    dist = math.sqrt((point[0]-median_tuple[0])**2+(point[1]-median_tuple[1])**2)
                    ...
                #all_distances=[get_distance_of_point_from_center(ids_sorted_by_possible_locs[item][loc]['coordinates'], center) for loc in ids_sorted_by_possible_locs[item]]
                ##print(harmonic_mean((all_distances)))
                #alle nehmen, die weniger als die Standardabweichung vom bereinigten Mittelwert entfernt sind.
                #hier überprüfen, ob selber Ahne!
                #alle rauswerfen, die weiter als Standardabweichung vom Mittelpunkt entfernt sind.
            ##print(provisional_new_ids)
    ##print()
    #for item in new_ids:
        ##print(item, new_ids[item])
    #für jeden Ort die möglichen Treffer vergleichen und den besten auswählen (z.B. durch Ausschluss von weiter entfernten?)

'''
    locs_dict={}
    for loc in locs:
        if loc not in locs_dict:
            locs_dict[loc]=text_to_process.count(loc)
    ##print(sorted(locs_dict.items(), key=lambda x:x[1], reverse=True))
    for loc in locs_dict:
        tf=(locs_dict[loc]/text_length)
        tf_dict[file][loc]=tf
        if loc not in df:
            df[loc]=1
        else:
            df[loc]+=1
    idf={}
    for term in df:
        if term not in idf:
            idf[term]=math.log(len(tf_dict)/df[term])
    tf_idf={}
    for file in tf_dict:
        tf_idf[file]={}
        for term in tf_dict[file]:
            tf_idf[file][term]=tf_dict[file][term]*idf[term]
        #tf_idf_max=max(tf_idf[file].values())
        #avg_tf_idf=sum(tf_idf[file].values())/len(tf_idf[file].values())
        for term in tf_dict[file]:
            #print(file, term, tf_idf[file][term], idf[term], tf_dict[file][term])
'''
