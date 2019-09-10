from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
import nltk
import re
import math
import spacy
from langdetect import detect
import os
import urllib
from urllib import request, parse
from statistics import mean
import json
import unicodedata
import xml.etree.cElementTree as ET
import time

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

def check_similarity_and_create_hierarchy(possible_loc, result, ids, locs):
    if result['@id'] not in ids:
        coordinates = []
        if 'prefLocation' in result:
            if 'coordinates' in result['prefLocation']:
                coordinates=result['prefLocation']['coordinates']
            if 'shape' in result['prefLocation']:
                coordinates=result['prefLocation']['shape']
        locs['loc'+result['@id'].split("/")[-1]]=possible_loc
        ids[result['@id']]=[result['@id']]
        all_ancestors=[]
        if 'parent' in result:
            ids[result['@id']]+=[result['parent']]
            ids[result['@id']]+=[result['parent']]
            id_of_ancestor=result['parent']
            all_ancestors.append(id_of_ancestor)
            while id_of_ancestor!="https://gazetteer.dainst.org/place/2042600":
                search_url = "https://gazetteer.dainst.org/doc/"+id_of_ancestor.split('/')[-1]+".json"
                req = urllib.request.Request(search_url)
                with urllib.request.urlopen(req) as response:
                    json_response=response.read()
                json_response=json_response.decode('utf-8')
                json_response=json.loads(json_response)
                id_of_ancestor=json_response['parent']
                all_ancestors.append(id_of_ancestor)
                if coordinates == []:
                    if 'prefLocation' in json_response:
                        if 'coordinates' in json_response['prefLocation']:
                            coordinates=json_response['prefLocation']['coordinates']
                        if 'shape' in json_response['prefLocation']:
                            coordinates=json_response['prefLocation']['shape']
            ids[result['@id']]+=all_ancestors
            if 'ancestors' in result:
                if all_ancestors[1:]!=result['ancestors']:
                    print('Fehlerhafte Hierachie:', result['@id'])
                    print('In den Daten:', result['ancestors'])
                    print('Ermittelt:', result['ancestors'])
            if ('ancestors' not in result) and (result['parent']!="https://gazetteer.dainst.org/place/2042600"):
                print(result['@id'], 'has no ancestors')
        else:
            print(result['@id'], 'has no parent')
        if coordinates == []:
            print('keine Koordinaten gefunden.', result['@id'])

    return ids, locs

def check_locs(list_of_possible_locs, ids, locs):
    for possible_loc in list_of_possible_locs:
        found_items=0
        possible_loc_before_parsing=possible_loc
        possible_loc=urllib.parse.quote(possible_loc, safe='').replace('%2F', '%20').replace('%21', '%20')
        search_url = "https://gazetteer.dainst.org/search.json?q="+possible_loc+"&offset=0&limit=150"
        req = urllib.request.Request(search_url)
        try:
            with urllib.request.urlopen(req) as response:
                json_response=response.read()
            json_response=json_response.decode('utf-8')
            json_response=json.loads(json_response)
            if 0<json_response['total']<100:
                for result in json_response['result']:
                    if remove_parentheses(remove_accents(result['prefName']['title']).split(',')[0].split('/')[0].strip())==remove_accents(possible_loc):
                        if 'types' in result:
                            ...
                            #print(result['types'])
                        if 'types' not in result:
                            ...

                            ids, locs = check_similarity_and_create_hierarchy(possible_loc, result, ids, locs)
                    else:
                        if 'names' in result.keys():
                            for name in result['names']:
                                if remove_parentheses(remove_accents(name['title']).split(',')[0].split('/')[0].strip())==remove_accents(possible_loc_before_parsing):
                                    check_similarity_and_create_hierarchy(possible_loc, result, ids, locs)
            elif json_response['total']==0:
                for part_of_possible_loc in possible_loc.split():
                    possible_loc_before_parsing=part_of_possible_loc
                    part_of_possible_loc=urllib.parse.quote(part_of_possible_loc, safe='')
                    search_url = "https://gazetteer.dainst.org/search.json?q="+part_of_possible_loc+"&offset=0&limit=150"
                    req = urllib.request.Request(search_url)
                    with urllib.request.urlopen(req) as response:
                        json_response=response.read()
                    json_response=json_response.decode('utf-8')
                    json_response=json.loads(json_response)
                    if 0<json_response['total']:
                        for result in json_response['result']:
                            if remove_parentheses(remove_accents(item['prefName']['title']).split(',')[0].split('/')[0].strip())==remove_accents(possible_loc_before_parsing):
                                check_similarity_and_create_hierarchy(possible_loc, result, ids, locs)
        except Exception as e:
            print(search_url)
            print('Error! Code: {c}, Message, {m}'.format(c = type(e).__name__, m = str(e)))
        #if found_items>1:
            #print(found_items, search_url)
    return locs, ids

xml=open('hierarchy.rdf', 'r')
soup=BeautifulSoup(xml, 'xml')
subjects=soup.find_all('rdf:Description')
subject_dict={}
#Wikipedia überprüfen, ob der Ortsname 1. eindeutig vergeben ist und Koordinaten vorhanden sind.
#for subject in subjects:
    #if subject.find('skos:narrower')!=None:
        #print(subject)
        #xml erstellen, das hierarchische Verhältnisse abbildet!!!
            #translator= Translator(to_lang="en", from_lang="de")
            #stemmed_subject_eng=stemmer.stem(RegexpTokenizer(r'\w+').tokenize(subject.find('skos:prefLabel').text)[0])

df={}
tf_dict={}
file_nr=0
#for file in os.listdir("eperiodica_text_files"):
for file in os.listdir('efb_text_files'):
    possible_locs=[]
    locs={}
    ids={}
    #if file_nr>10:
        #continue
    file_nr+=1
    #print(file)
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
    #print(sorted(nouns_dict.items(), key=lambda x:x[1], reverse=True))
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
          #https://de.wikipedia.org/?curid=1082177
    locs_dict={}
    for loc in locs:
        if loc not in locs_dict:
            locs_dict[loc]=text_to_process.count(loc)
    #print(sorted(locs_dict.items(), key=lambda x:x[1], reverse=True))
    for loc in locs_dict:
        tf=(locs_dict[loc]/text_length)
        tf_dict[file][loc]=tf
        if loc not in df:
            df[loc]=1
        else:
            df[loc]+=1
    #print(sorted(tf_dict[file].items(), key=lambda x:x[1], reverse=True))
    #print(df)
    root = ET.Element('loc2042600')
    tree = ET.ElementTree(root)
    all_tags=['loc2042600']
    for item in ids:
        ids[item].reverse()
        ids[item]=['loc'+link.split('/')[-1] for link in ids[item]]
        if ids[item][0]=='loc2042600':
            if text_to_process.count(locs[ids[item][-1]])>1:
                for loc in ids[item][1:]:
                    if loc not in all_tags:
                        all_tags.append(loc)
                        parent = [elem for elem in tree.iter(ids[item][ids[item].index(loc)-1])][0]
                        if loc != ids[item][-1]:
                            ET.SubElement(parent, loc, level=str(ids[item].index(loc)))
                        else:
                            ET.SubElement(parent, loc, level='last', count=str(text_to_process.count(locs[loc])))
    tree = ET.ElementTree(root)
    tree.write('efb_xml_files/'+file.replace('.txt', '')+'_geo_locations.xml')

'''
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
        print(file, term, tf_idf[file][term], idf[term], tf_dict[file][term])
'''

# Germania bis 1955 verschlagworten, Abgleich mit vorhandenen Schlagworten im Katalog!!!