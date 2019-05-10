from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
import nltk
#from translate import Translator
import json
import spacy
#import urllib.parse, urllib.request
nlp = spacy.load('de_core_news_sm')
stemmer=nltk.stem.cistem.Cistem(case_insensitive=False)
#ner=spacy.load("custom_ner_model")
#nltk.download('stopwords')
#nltk.download('averaged_perceptron_tagger')
#nltk.download('punkt')
with open('frequent_words.json', 'r') as frequent_words_file:
    frequent_words_dict=json.load(frequent_words_file)
stopwords=stopwords.words('german')
xml=open('hierarchy.rdf', 'r')
soup=BeautifulSoup(xml, 'xml')
subjects=soup.find_all('rdf:Description')
subject_list=[]
tokenized_stemmed_subject_wordlist={}
#Wikipedia überprüfen, ob der Ortsname 1. eindeutig vergeben ist und zweitens "Geographie" als Überschrift im Artikel auftaucht.
for subject in subjects:
    if subject.find('skos:prefLabel')!=None:
        if len(RegexpTokenizer(r'\w+').tokenize(subject.find('skos:prefLabel').text))==1:
            stemmed_subject=stemmer.stem(RegexpTokenizer(r'\w+').tokenize(subject.find('skos:prefLabel').text)[0])
            if stemmed_subject not in tokenized_stemmed_subject_wordlist:
                tokenized_stemmed_subject_wordlist[stemmed_subject]=RegexpTokenizer(r'\w+').tokenize(subject.find('skos:prefLabel').text)[0]
            #translator= Translator(to_lang="en", from_lang="de")
            #stemmed_subject_eng=stemmer.stem(RegexpTokenizer(r'\w+').tokenize(subject.find('skos:prefLabel').text)[0])
text_to_process=(open('test.txt', 'r')).read().split('Objekttyp: Article')[0]
text_to_process=text_to_process.replace("-\n", "")
sentences=nltk.sent_tokenize(text_to_process)
text_length=len(RegexpTokenizer(r'\w+').tokenize(text_to_process))
nouns={}
stemmed_nouns={}
stemmed_locs={}
locs={}
for sentence in sentences:
    tagged_sentence=nlp(sentence)
    for token in tagged_sentence:
        print(token.pos)
        if token.pos_=="NOUN":
            token_text=token.text.split("-")[0]
            if token_text in nouns:
                nouns[token_text]+=1
            else:
                nouns[token_text]=1
# lemmatizer bauen auf Basis von Duden?
# abfragen auf Koordinaten und wenn diese vorhanden sind,
# Schlagwort übernehmen. außerdem selbst lemmatizer bauen für Ortsnamen, falls möglich.
# Auswertung Gesamtkorpus vornehmen.
#nach stemming vergleichen und alle Worte auf die Grundform zurückführen.
import requests

S = requests.Session()
#untersuchen, ob durch tf-idf gleich gerankte Ortsangaben vorkommen, dann erst mit Wikipedia-URL suchen
URL = "https://de.wikipedia.org/w/api.php"
doc = nlp(text_to_process)
for ent in doc.ents:
    if ent.label_ in ["LOC", "GPE"]:
        TITLE = ent.text
        if "-" in TITLE:
            TITLE=TITLE.split("-")[0]
        PARAMS = {
            'action':"query",
            'titles': TITLE,
            'format':"json",
            'prop':"coordinates",
        }
        R = S.get(url=URL, params=PARAMS)
        DATA = R.json()
        if len(DATA['query']['pages'])==1:
            pageid=list(DATA['query']['pages'].keys())[0]
            if pageid!=-1:
                if 'coordinates' in DATA['query']['pages'][pageid].keys():
                    if TITLE in locs.keys():
                        locs[TITLE]+=1
                    else:
                        locs[TITLE]=1
                    #https://de.wikipedia.org/?curid=1082177
#Ortsangaben am Bindestrich trennen und den vorderen Teil verwenden.
subject_nr=0
subject_frequency={}
for noun in nouns:
    stemmed_noun=stemmer.stem(noun)
    for key in stemmed_nouns:
        if stemmer.stem(key)==stemmed_noun:
            print(noun, stemmed_noun, key)
        else:
            if len(noun)<len(key):
                ...

#translator= Translator(to_lang="fr", from_lang="de")
#translator.translate("Bronzezeit")
'''for word in tokenized_text_list:
    if len(word)>=5:
        try:
            int(word)
        except:
            stemmed_word=stemmer.stem(word)
            if len(stemmed_word)>4 and stemmed_word not in stopwords and stemmed_word not in frequent_words_dict:
                try:
                    new_subject=tokenized_stemmed_subject_wordlist[stemmed_word]
                    #print(new_subject)
                    subject_nr+=1
                    if new_subject not in subject_frequency.keys():
                        subject_frequency[new_subject]=1
                    else:
                        subject_frequency[new_subject]+=1
                except: continue'''
#print(DATA)
#print(subject_frequency)
for key in subject_frequency.keys():
    if subject_frequency[key]>=3:
        for item in subject_frequency.keys():
            if key.lower() in item:
                continue
            else:
                print(key, subject_frequency[key], subject_frequency[key]/len(tokenized_stemmed_subject_wordlist))
#für alle Titel: pdf abrufen, in Text umwandeln, durchsuchen, alle subjects übersetzen in die geläufigsten Sprechen (de, en, fr, it, es)

