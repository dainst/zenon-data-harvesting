from PIL import Image
import pytesseract
import os
import language_codes
from langdetect import detect
import pdftotext
import urllib.parse, urllib.request
from bs4 import BeautifulSoup

out = None
issues = []
url = 'https://publications.dainst.org/journals/index.php/efb'
record_nr = 0
user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
values = {'name': 'Helena Nebel',
          'location': 'Berlin',
          'language': 'Python'}
headers = {'User-Agent': user_agent}
data = urllib.parse.urlencode(values)
data = data.encode('ascii')
req = urllib.request.Request(url, data, headers)
with urllib.request.urlopen(req) as response:
    journal_page = response.read()
journal_page = journal_page.decode('utf-8')
journal_soup = BeautifulSoup(journal_page, 'html.parser')
h4_elements = journal_soup.find_all('h4')
h4_elements=h4_elements[:-1]
list_elements=[]
for element in h4_elements:
    list_elements.append(element.find('a')['href'])
already_harvested=["https://publications.dainst.org/journals/index.php/efb/issue/view/166", "https://publications.dainst.org/journals/index.php/efb/issue/view/162", "https://publications.dainst.org/journals/index.php/efb/issue/view/2"]
for list_element in list_elements:
    #if list_elements.index(list_element)>=1:
    #break
    if list_element in already_harvested:
        continue
    else:
        url = list_element
        req = urllib.request.Request(url, data, headers)
        with urllib.request.urlopen(req) as response:
            issue_page = response.read().decode('utf-8')
        issue_soup = BeautifulSoup(issue_page, 'html.parser')
        year=issue_soup.find('h2').text
        issue=issue_soup.find_all('h3')[0].text.replace("zikel ", "c.")
        issue_file_name = year + "_" + issue
        if issue_file_name not in issues:
            out = open("efb/"+issue_file_name+".mrc", 'wb')
        article_nr = 0
        for article in issue_soup.find_all('table', class_='tocArticle')[1:]:
            pdf = article.find('div', class_='tocGalleys').find('a')['href'].strip()
            article_url = article.find('div', class_='tocTitle').find('a')['href'].strip()
            req = urllib.request.Request(article_url, data, headers)
            with urllib.request.urlopen(req) as response:
                issue_page = response.read().decode('utf-8')
            article_soup = BeautifulSoup(issue_page, 'html.parser')
            title = article_soup.find('meta', attrs={'name': 'citation_title'})['content']

            webFile = urllib.request.urlopen(pdf)
            pdfFile = open("efb_files/"+year+"_"+title+'.pdf', 'wb')
            pdfFile.write(webFile.read())
            webFile.close()
            pdfFile.close()
            PDF_file = "efb_files/"+year+"_"+title+'.pdf'

            # Load your PDF
            with open(PDF_file, "rb") as f:
                pdf = pdftotext.PDF(f)

            # If it's password-protected
            #with open("secure.pdf", "rb") as f:
                #pdf = pdftotext.PDF(f, "secret")

                # How many pages?
                print(len(pdf))

                # Iterate over all the pages
                for page in pdf:
                    print(page)

                # Read some individual pages
                print(pdf[0])
                print(pdf[1])

                # Read all the text into one string
                print("\n\n".join(pdf))


'''
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
