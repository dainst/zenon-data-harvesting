from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
import nltk
import re
import math
#from translate import Translator
import json
import spacy
from langdetect import detect
import os
import requests
from statistics import mean
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

def check_locs(list_of_possible_locs, locs):
    for possible_loc in list_of_possible_locs:
        S = requests.Session()
        #untersuchen, ob durch tf-idf gleich gerankte Ortsangaben vorkommen, dann erst mit Wikipedia-URL suchen
        URL = "https://de.wikipedia.org/w/api.php"
        PARAMS = {
            'action':"query",
            'titles': possible_loc,
            'format':"json",
            'prop':"coordinates",
        }
        R = S.get(url=URL, params=PARAMS)
        DATA = R.json()
        try:
            if len(DATA['query']['pages'])==1:
                pageid=list(DATA['query']['pages'].keys())[0]
                if pageid!=-1:
                    if 'coordinates' in DATA['query']['pages'][pageid].keys():
                        locs.append(TITLE)
        except:
            print("Die Anfrage für die Ortsangabe", TITLE, "ist gescheitert.")
    return locs

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
    locs=[]
    #if file_nr>10:
        #continue
    file_nr+=1
    #print(file)
    tf_dict[file]={}
    text_to_process=(open('efb_text_files/'+file, 'r')).read()
    text_to_process=text_to_process.replace("-\n", "")
    text_to_process=text_to_process.replace("\n", " ")
    remove_parentheses = re.compile(".*?\((.*?)\)")
    result = re.findall(remove_parentheses, text_to_process)
    for item in result:
        text_to_process=text_to_process.replace("("+item+")", "")
    try:
        lang=detect(text_to_process)
    except:
        lang="de"
    text_length=len(RegexpTokenizer(r'\w+').tokenize(text_to_process))
    nlp=None
    nouns=[]
    if lang in ["de", "en", "fr", "it", "es", "nl"]:
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
                            if token.text not in possible_locs:
                                possible_locs.append(token_text)
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



    doc = nlp(text_to_process)
    for ent in doc.ents:
        if ent.label_ in ["LOC", "GPE"]:
            TITLE = ent.text
            if "-" in TITLE:
                TITLE=TITLE.split("-")[0]
            for part_of_title in TITLE.split():
                if part_of_title not in possible_locs:
                    possible_locs.append(part_of_title)

    locs = check_locs(possible_locs, locs)

          #https://de.wikipedia.org/?curid=1082177
    locs_dict={}
    for loc in locs:
        if loc not in locs_dict:
            locs_dict[loc]=text_to_process.count(loc)
    #print(sorted(locs_dict.items(), key=lambda x:x[1], reverse=True))
    loc_tf_dict={}
    for loc in locs_dict:
        tf=(locs_dict[loc]/text_length)
        loc_tf_dict[loc]=tf
    for loc in loc_tf_dict:
        tf_dict[file][loc]=loc_tf_dict[loc]
        if loc not in df:
            df[loc]=1
        else:
            df[loc]+=1
    #print(sorted(tf_dict[file].items(), key=lambda x:x[1], reverse=True))
idf={}
for term in df:
    if term not in idf:
        idf[term]=math.log(len(tf_dict)/df[term])
tf_idf={}
for file in tf_dict:
    tf_idf[file]={}
    for term in tf_dict[file]:
        tf_idf[file][term]=tf_dict[file][term]*idf[term]
    tf_idf_max=max(tf_idf[file].values())
    avg_tf_idf=sum(tf_idf[file].values())/len(tf_idf[file].values())
    for term in tf_dict[file]:
        print(file, term, tf_idf[file][term], idf[term], tf_dict[file][term])

    #translator= Translator(to_lang="fr", from_lang="de")
    #translator.translate("Bronzezeit")
#Rating wird mit merh Datensätzen vermutlich besser.
