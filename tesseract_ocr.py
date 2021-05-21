from PIL import Image
import pytesseract
import os
import time
import language_codes
from langdetect import detect

for dirname in os.listdir('pages_jpg'):
    lang_code=None
    txt=open("eperiodica_text_files/"+dirname+".txt", mode='w+', encoding='utf-8')
    jpg_nr=0
    for filename in os.listdir('pages_jpg/'+dirname):
        jpg_nr+=1
        text = str(((pytesseract.image_to_string(Image.open('pages_jpg/'+dirname+'/'+filename),lang="deu"))))
        try:
            language=language_codes.resolve(detect(text))
            #print(language)
            if language!='ger':
                if language=='fre':
                    lang_code='fra'
                if language=='ita':
                    lang_code='ita'
                if language=='dut':
                    lang_code='nld'
                if language=='spa':
                    lang_code='spa'
                text = str(((pytesseract.image_to_string(Image.open('pages_jpg/'+dirname+'/'+filename),lang=lang_code))))
            txt.write(text)
        except:
            continue
    txt.close()
'''
nlp_de = spacy.load('de_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')
nlp_fr = spacy.load('fr_core_news_sm')
nlp_es = spacy.load('es_core_news_sm')
nlp_it = spacy.load('it_core_news_sm')
nlp_nl = spacy.load('nl_core_news_sm')
amh
ara
asm
aze
aze-cyrl
bel
ben
bod
bos
bul
cat
ceb
ces
chi-sim
chi-tra
chr
cym
dan
dan-frak
deu
deu-frak
dev
dzo
ell
enm
epo
est
eus
fas
fin
fra
frk
frm
gle
gle-uncial
glg
grc
guj
hat
heb
hin
hrv
hun
iku
ind
isl
ita
ita-old
jav
jpn
kan
kat
kat-old
kaz
khm
kir
kor
kur
lao
lat
lav
lit
mal
mar
mkd
mlt
msa
mya
nep
nld
nor
ori
pan
pol
por
pus
ron
rus
san
sin
slk
slk-frak
slv
spa
spa-old
sqi
srp
srp-latn
swa
swe
syr
tam
tel
tgk
tgl
tha
tir
tur
uig
ukr
urd
uzb
uzb-cyrl
vie
yid
'''
