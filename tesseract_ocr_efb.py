from PIL import Image
import pytesseract
import os
import language_codes
from langdetect import detect

for dirname in os.listdir('pages_jpg_efb'):
    print(dirname)
    lang_code=None
    txt=open("efb_text_files/"+dirname+".txt", mode='w+', encoding='utf-8')
    lang = language_codes.resolve(detect(dirname[4:]))
    if lang=='fre':
        lang_code='fra'
    elif lang=='ita':
        lang_code='ita'
    elif lang=='dut':
        lang_code='nld'
    elif lang=='spa':
        lang_code='spa'
    else:
        lang_code='deu'
    print(lang_code)
    jpg_nr=0
    for filename in sorted(os.listdir('pages_jpg_efb/'+dirname)):
        jpg_nr+=1
        try:
            text = str(pytesseract.image_to_string(Image.open('pages_jpg_efb/'+dirname+'/'+filename),lang=lang_code))
            txt.write(text)
        except:
            print('Umwandlung gescheitert')
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
