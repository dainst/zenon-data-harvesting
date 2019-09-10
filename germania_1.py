import urllib.parse, urllib.request
from pymarc import Record, Field
import arrow
import csv
import language_codes
# import nltk
from nltk.tokenize import RegexpTokenizer
from bs4 import BeautifulSoup
import ast
import spacy
from langdetect import detect

# from langdetect import detect_langs
# import polyglot
# from polyglot.text import Text, Word

subject_table = open("records/subject_table.csv", "w")
subject_writer = csv.writer(subject_table, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
nlp_de = spacy.load('de_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')
nlp_fr = spacy.load('fr_core_news_sm')
nlp_es = spacy.load('es_core_news_sm')
nlp_it = spacy.load('it_core_news_sm')
nlp_nl = spacy.load('nl_core_news_sm')
nlp_xx = spacy.load('xx_ent_wiki_sm')

language_articles = {'eng': ['the', 'a', 'an'], 'fre': ['la', 'le', 'les', 'un', 'une', 'l\'', 'il'],
                     'spa': ['el', 'lo', 'la', 'las', 'los',
                             'uno' 'un', 'unos', 'unas', 'una'], 'ger': ['das', 'der', 'ein', 'eine', 'die'],
                     'ita': ['gli', 'i', 'le', 'la', 'l\'',
                             'lo', 'il', 'gl\'', 'l']}
unresolved_titles = {
    "H. G. Bandi und J. Maringer, Kunst der Eiszeit. Levantekunst. Arktische Kunst": "H. G. Bandi und J. Maringer",
    "C. F. A. Schaeffer, Stratigraphie Comparée et Chronologie de l’Asie Occidentale (IIIe et IIe millénaires)": "C. F. A. Schaeffer",
    "G. Freund, Die Blattspitzen des Paläolithikums in Europa": "G. Freund",
    "Cl. F.-A. Schaeffer, Ugaritica II": "Cl. F.-A. Schaeffer",
    "Siegfried J. De Laet, Portorium. Etude sur l'organisation douanière chez  les Romains surtout à l'époque du Haut-Empire": "Siegfried J. De Laet",
    "K. H. Jacob-Friesen, Die Altsteinzeitfunde aus dem Leinetal bei Hannover": "K. H. Jacob-Friesen",
    "Dorin Popescu, Die frühe und mittlere Bronzezeit in Siebenbürgen": "Dorin Popescu",
    "Mozsolics Amália, A Kisapostagi Korabronzkori Urnateinető, Függelék: Méri István, A mészbetétágy elkészítésének módja a Kisapostagi edényeken": "Mozsolics Amália",
    "Thesaurus Antiquitatum Transsilvanicarum Teil 1. Praehistorica": None,
    "Janós Dombay, A Zengővárkonyi őskori telep és temető (The Prehistoric Settlement and Cemetery at Zengővárkony)": "Janós Dombay",
    "K. H. Jacob-Friesen, Einführung in Niedersachsens Urgeschichte. Darstellungen aus Niedersachsens Urgeschichte. Band 1": "K. H. Jacob-Friesen",
    "Gotlands Bildsteine. Band 1": None, "Oleh Kandyba, Schipenitz": "Oleh Kandyba",
    "Marg. Bachmann, Die Verbreitung der slavischen Siedlungen in Nordbayern": "Marg. Bachmann",
    "Eugen v. Frauenholz, Das Heerwesen der germanischen Frühzeit, des Frankenreiches und des ritterlichen Zeitalters": "Eugen v. Frauenholz",
    "R. Neuville - A. Rühlmann, LaPlace du Paleolithique Ancien dans le Quaternaire Marocain": "R. Neuville und A. Rühlmann",
    "Saint Catharine’s Hill, Winchester": None,
    "Miles Burkitt and V. Gordon Childe, A Chronological Table of Prehistory": "Miles Burkitt und V. Gordon Childe",
    "W. Vermeulen, Een romeinsch Grafveld op den Hunnerberg te Nymegen": "W. Vermeulen"}


def swagger_search_review(search_title, search_authors, print_title, recent_record, year):
    url = u'https://zenon.dainst.org/api/v1/search?lookfor=title%3A' + search_title + '%20AND%20author%3A' + search_authors + '%20NOT%20title%3A[Rez.zu]' + '%20AND%20publishDate%3A%5B*%20TO%20' + year + '%5D&type=AllFields&sort=relevance&page=1&limit=20&prettyPrint=false&lng=de'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        journal_page = response.read()
    journal_page = journal_page.decode('utf-8')
    resultcount = str(ast.literal_eval(str(journal_page))["resultCount"])
    if resultcount == '1':
        sysnumber = str(ast.literal_eval(str(journal_page))["records"][0]["id"])
        recent_record.add_field(Field(tag='LKR', indicators=[' ', ' '],
                                      subfields=['a', 'UP', 'b', sysnumber, 'l', 'DAI01',
                                                 'm', 'Rezension', 'n', print_title]))
    return resultcount


# definition für create_review_title


def swagger_find_reviewed_article(recent_record, title, rev_auth, editors, year):
    search_title = ""
    word_nr = 0
    search_authors = ""
    if rev_auth != None:
        title = title.replace(rev_auth + ", ", "").replace("R. Neuville - A. Rühlmann, ", "").replace(rev_auth + ". ","")
        print_authors = ""
        for auth in rev_auth.split(" und "):
            print_authors += auth.rsplit(" ", 1)[1] + ", " + auth.rsplit(" ", 1)[0] + " "
            for name in auth.split(" "):
                name = urllib.parse.quote(name, safe='')
                if ("." not in name):
                    search_authors = search_authors + "+" + name
        search_authors = search_authors.strip("+")
        print_title = "[Rez.zu:]" + print_authors.strip() + ": " + title
    elif editors != None:
        title.strip()
        print_editors = ""
        for edit in editors.split(" und "):
            print_editors += edit.rsplit(" ", 1)[1] + ", " + edit.rsplit(" ", 1)[0] + " "
        print_title = "[Rez.zu:]" + print_editors.strip() + "(Hrsg.): " + title
    else:
        print_title = "[Rez.zu:]" + title
    for word in RegexpTokenizer(r'\w+').tokenize(title):
        if (word_nr < 7) and (len(word) > 3):
            word = urllib.parse.quote(word, safe='')
            search_title = search_title + "+" + word
            word_nr += 1
    search_title = search_title.strip("+")
    resultcount = swagger_search_review(search_title, search_authors, print_title, recent_record, year)
    if resultcount == '0':
        search_title = ""
        word_nr = 0
        adjusted_title = title.split(". ")[0].split(":")[0]
        for word in RegexpTokenizer(r'\w+').tokenize(adjusted_title):
            word = urllib.parse.quote(word, safe='')
            if (word_nr < 8) and (len(word) > 3):
                search_title = search_title + "+" + word
                word_nr += 1
        if word_nr >= 2:
            search_title = search_title.strip("+")
        resultcount = swagger_search_review(search_title, search_authors, print_title, recent_record, year)
    return resultcount


def create_245_and_246(recent_record, title, nonfiling_characters, author_nr):
    recent_record.add_field(Field(tag='245', indicators=[str(author_nr), nonfiling_characters], subfields=['a', title]))


def search_subject(year, search_subject_title, search_subject_person, title):
    s_title = urllib.parse.quote(title, safe='')
    url = u'https://zenon.dainst.org/api/v1/search?lookfor=title%3A' + s_title + '%20AND%20author%3A' + search_subject_person.replace(
        " ",
        "+") + '%20AND%20publishDate%3A' + year + '%5D&type=AllFields&sort=relevance&page=1&limit=20&prettyPrint=false&lng=de'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        journal_page = response.read()
    journal_page = journal_page.decode('utf-8')
    resultcount = str(ast.literal_eval(str(journal_page))["resultCount"])
    if resultcount == '1':
        sysnumber = str(ast.literal_eval(str(journal_page))["records"][0]["id"])
        url = "http://swb.bsz-bw.de/sru/DB=2.1/username=/password=/?query=pica.ejh+%3D+%22" + year + "%22+and+pica.tit+%3D+" + search_subject_title + "+and+pica.pne+%3D+%22" + search_subject_person + "%22&version=1.1&operation=searchRetrieve&stylesheet=http%3A%2F%2Fswb.bsz-bw.de%2Fsru%2FDB%3D2.362%2F%3Fxsl%3DsearchRetrieveResponse&recordSchema=marc21&maximumRecords=10&startRecord=1&recordPacking=xml&sortKeys=none&x-info-5-mg-requestGroupings=none"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            subject_page = response.read()
        subject_page = subject_page.decode('utf-8')
        subject_soup = BeautifulSoup(subject_page, 'html.parser')
        if len(subject_soup.find_all('datafield', tag="245")) == 0:
            search_subject_title = search_subject_title.split(".")[0].split("%2C%20")[0].split("%28")[0]
            url = "http://swb.bsz-bw.de/sru/DB=2.1/username=/password=/?query=pica.ejh+%3D+%22" + year + "%22+and+pica.tit+%3D+" + search_subject_title + "+and+pica.pne+%3D+%22" + search_subject_person + "%22&version=1.1&operation=searchRetrieve&stylesheet=http%3A%2F%2Fswb.bsz-bw.de%2Fsru%2FDB%3D2.362%2F%3Fxsl%3DsearchRetrieveResponse&recordSchema=marc21&maximumRecords=10&startRecord=1&recordPacking=xml&sortKeys=none&x-info-5-mg-requestGroupings=none"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                subject_page = response.read()
            subject_page = subject_page.decode('utf-8')
            subject_soup = BeautifulSoup(subject_page, 'html.parser')
        if subject_soup.find_all('datafield', tag="689") != None:
            if len(subject_soup.find_all('datafield', tag="689")) != 0:
                print('689')
                print(sysnumber)
                row = [sysnumber]
                for subject in subject_soup.find_all('datafield', tag="689"):
                    if subject.find('subfield', code="D") != None:
                        indicator = subject.find('subfield', code="D").text
                        subject_name = subject.find('subfield', code="a").text
                        if "," in subject_name:
                            subject_name = subject_name.replace(",", "|")
                        subject_tuple = (indicator, subject_name)
                        if subject_name not in row:
                            row.append(indicator)
                            row.append(subject_name)
                subject_writer.writerow(row)


def determine_nonfiling_characters(recent_record, title, year, review):
    nonfiling_characters = 0
    language = language_codes.resolve(article_soup.find('meta', attrs={'name': 'DC.Language'})['content'])
    recent_record.add_field(Field(tag='041', indicators=['1', ' '], subfields=['a', language]))
    if language in language_articles.keys():
        first_word = (title.split()[0]).lower()
        if first_word in language_articles[language]:
            nonfiling_characters = str(len(first_word) + 1)
    if review == True:
        data_008 = str(time_str) + 's' + year + '    ' + 'gw ' + ' |   oo    |    |' + language + ' d'
    else:
        data_008 = str(time_str) + 's' + year + '    ' + 'gw ' + ' |   o     |    |' + language + ' d'
    recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
    if review == True:
        nonfiling_characters = '0'
    return nonfiling_characters


def create_new_record(article_soup, out, category, url):
    doi = None
    pdf = None
    pages = None
    volume = None
    review = False
    abstract_text = article_soup.find('meta', attrs={'name': 'DC.Description'})['content']
    recent_record = Record(force_utf8=True)
    recent_record.add_field(
        Field(tag='336', indicators=[' ', ' '], subfields=['a', 'text', 'b', 'txt', '2', 'rdacontent']))
    recent_record.add_field(
        Field(tag='337', indicators=[' ', ' '], subfields=['a', 'computer', 'b', 'c', '2', 'rdamedia']))
    recent_record.add_field(
        Field(tag='338', indicators=[' ', ' '], subfields=['a', 'online resource', 'b', 'cr', '2', 'rdacarrier']))

    authors = article_soup.find_all('meta', attrs={'name': 'citation_author'})
    author_names = []
    for author in authors:
        author_names.append(author['content'])
    authors = author_names
    title = article_soup.find('meta', attrs={'name': 'citation_title'})['content']
    search_subject_title = urllib.parse.quote(title, safe='')
    year = article_soup.find('meta', attrs={'name': 'citation_date'})['content']
    if article_soup.find('meta', attrs={'name': 'citation_volume'}) != None:
        volume = article_soup.find('meta', attrs={'name': 'citation_volume'})['content']
    if len(article_soup.find_all('meta', attrs={'name': 'citation_issue'})) != 0:
        issue = article_soup.find('meta', attrs={'name': 'citation_issue'})['content']
    else:
        issue = None
    if article_soup.find('meta', attrs={'name': 'citation_doi'}) != None:
        doi = 'https://doi.org/' + article_soup.find('meta', attrs={'name': 'citation_doi'})['content']
        if doi != None:
            recent_record.add_field(Field(tag='024', indicators=['7', ' '], subfields=['a', doi, '2', 'doi']))
    abstract = article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']
    if article_soup.find('meta', attrs={'name': 'citation_pdf_url'}) != None:
        pdf = article_soup.find('meta', attrs={'name': 'citation_pdf_url'})['content']
    if article_soup.find('meta', attrs={'name': 'DC.Identifier.pageNumber'}) != None:
        pages = article_soup.find('meta', attrs={'name': 'DC.Identifier.pageNumber'})['content']
    search_subject_person = ""
    author_nr = 0
    for author in authors:
        if author != "Die Redaktion":
            if author_nr == 0:
                search_subject_person += urllib.parse.quote(author.split()[-1], safe='')
            author = author.rsplit(" ", 1)[1] + ", " + author.rsplit(" ", 1)[0]
            if author_nr == 0:
                recent_record.add_field(Field(tag='100', indicators=['1', ' '], subfields=['a', author]))
                author_nr += 1
            else:
                recent_record.add_field(Field(tag='700', indicators=['1', ' '], subfields=['a', author]))
                author_nr = author_nr

    date_published_online = article_soup.find('div', class_='published').find('div', class_='value').text.strip()
    recent_record.add_field(Field(tag='006', indicators=None, data='m        u        '))
    recent_record.add_field(Field(tag='040', indicators=[' ', ' '], subfields=['a', 'DE-16', 'd', 'DE-2553']))

    recent_record.add_field(Field(tag='533', indicators=[' ', ' '],
                                  subfields=['a', 'Online edition', 'b', 'Heidelberg', 'c', 'Heidelberg UB', 'd',
                                             date_published_online[:4], 'e', 'Online resource']))
    recent_record.leader = recent_record.leader[:5] + 'nab a       uu ' + recent_record.leader[20:]
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'arom']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', '2019xhnxgerm']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'daiauf8']))
    recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'online publication']))
    recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'tc'))
    print_title = title
    if category == "Besprechungen" or category == "Rezensionen / Reviews / Comptes rendus":
        editorship = False
        rev_auth = None
        editors = None
        review = True
        for title in title.split(" / "):
            editors = None
            for editorship_word in ["Hrsg, von ", "Hrsg. von ", "Herausgegeben von ", "hrsg. von "]:
                if editorship_word in title:
                    editorship = True
                    if title == "Heinrich Schliemann. Briefwechsel. Aus dem Nachlaß in Auswahl hrsg. von Ernst Meyer. Band 1. Von 1842-1875":
                        title = title.replace(". Band 1. Von 1842-1875", "")
                    editors = title.split(editorship_word)[1]
            title = title.strip()
            lang = detect(title)
            nlp = None
            if lang in ["de", "en", "fr", "it", "es", "nl"]:
                if lang == "de":
                    nlp = nlp_de
                elif lang == "en":
                    nlp = nlp_en
                elif lang == "fr":
                    nlp = nlp_fr
                elif lang == "it":
                    nlp = nlp_it
                elif lang == "es":
                    nlp = nlp_es
                elif lang == "nl":
                    nlp = nlp_nl
                tagged_sentence = nlp(title)
                propn = False
                punct = False
                for word in tagged_sentence:
                    print(word.pos_)
                    if propn == True and word.text == "und":
                        continue
                    if punct == True:
                        break
                    if word.pos_ not in ["PUNCT", "PROPN"]:
                        break
                    if word.pos_ == "PUNCT" and propn == True and word.text != "-":
                        punct = True
                        if len(title.split(word.text)[0].split()) > 1:
                            rev_auth = title.split(word.text)[0]
                    if word.pos_ == "PROPN":
                        propn = True
                    else:
                        propn = False
                if rev_auth == None:
                    for ent in tagged_sentence.ents:
                        if ent.label_ == "PER":
                            if title.startswith(ent.text) == True:
                                if len(ent.text.split()) > 1:
                                    rev_auth = ent.text
                        break
            else:
                nlp = nlp_xx
                tagged_sentence = nlp(title)
                for ent in tagged_sentence.ents:
                    if ent.label_ == "PER":
                        if title.startswith(ent.text) == True:
                            if len(ent.text.split()) > 1:
                                rev_auth = ent.text
                        break
            if editorship == True:
                title = title.split(editorship_word)[0]
                rev_auth = None
            if title in unresolved_titles:
                rev_auth = unresolved_titles[title]
            swagger_find_reviewed_article(recent_record, title, rev_auth, editors, year)
        if rev_auth != None:
            title = title.replace(rev_auth + ", ", "").replace("R. Neuville - A. Rühlmann, ", "").replace(
                rev_auth + ". ", "").replace("Miles Burkitt and V. Gordon Childe, ", "")
            print_authors = ""
            for auth in rev_auth.split(" und "):
                print_authors += auth.rsplit(" ", 1)[1] + ", " + auth.rsplit(" ", 1)[0] + ", "
            print_title = "[Rez.zu:]" + print_authors.strip(", ") + ": " + title
        elif editors != None:
            title.strip()
            print_editors = ""
            for edit in editors.split(" und "):
                print_editors += edit.rsplit(" ", 1)[1] + ", " + edit.rsplit(" ", 1)[0] + ", "
            print_title = "[Rez.zu:]" + print_editors.strip(", ") + "(Hrsg.): " + title
        else:
            print_title = "[Rez.zu:]" + title
    nonfiling_characters = determine_nonfiling_characters(recent_record, title, year, review)
    create_245_and_246(recent_record, print_title, nonfiling_characters, author_nr)
    if review != True and "Fundchronik" not in title:
        search_subject(year, search_subject_title, search_subject_person, title)
    publishers = {'1904': ['Frankfurt am Main', 'Baer'], '1921': ['Bamberg', 'Buchner'],
                  '1932': ['Berlin', 'de Gruyter'], '1976': ['Mainz', 'von Zabern'],
                  '2011': ['Darmstadt', 'von Zabern'],
                  '2013': ['Frankfurt am Main', 'Henrich Editionen']}
    years_published_in = list(publishers.keys())
    years_published_in.sort(reverse=True)
    for key in years_published_in:
        if year >= key:
            recent_record.add_field(Field(tag='260', indicators=[' ', ' '],
                                          subfields=['a', publishers[key][0], 'b', publishers[key][1], 'c', year]))
            break
    if (doi != None) and (abstract_text.strip() != "-"):
        recent_record.add_field(Field(tag='856', indicators=['4', '1'],
                                      subfields=['z', 'Abstract', 'u', abstract]))
    if pdf != None:
        recent_record.add_field(Field(tag='856', indicators=['4', '1'],
                                      subfields=['z', 'application/pdf', 'u', pdf]))
    recent_record.add_field(Field(tag='856', indicators=['4', '1'],
                                  subfields=['z', 'Table of Contents', 'u', url]))

    if volume != None:
        if category == "Besprechungen" or category == "Rezensionen / Reviews / Comptes rendus":
            recent_record.add_field(Field(tag='LKR', indicators=[' ', ' '],
                                          subfields=['a', 'ANA', 'b', '001555096', 'l', 'DAI01',
                                                     'm', print_title, 'n', '[Rez.in]: Germania' + ', ' +
                                                     volume + ' (' + year + ')']))
        else:
            recent_record.add_field(Field(tag='LKR', indicators=[' ', ' '],
                                          subfields=['a', 'ANA', 'b', '001555096', 'l', 'DAI01',
                                                     'm', print_title, 'n', 'Germania' + ', ' +
                                                     volume + ' (' + year + ')']))
    else:
        if category == "Besprechungen" or category == "Rezensionen / Reviews / Comptes rendus":
            recent_record.add_field(Field(tag='LKR', indicators=[' ', ' '],
                                          subfields=['a', 'ANA', 'b', '001555096', 'l', 'DAI01',
                                                     'm', print_title, 'n', '[Rez.in]: Germania, ' + year]))
        else:
            recent_record.add_field(Field(tag='LKR', indicators=[' ', ' '],
                                          subfields=['a', 'ANA', 'b', '001555096', 'l', 'DAI01',
                                                     'm', print_title, 'n', 'Germania, ' +
                                                     year]))
    if issue == None:
        issue = article_soup.find('a', class_='title').text.split("Nr. ")[1].split(" (")[0]
    recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', 'Fasc. ' + issue + ', ' + pages]))
    out.write(recent_record.as_marc21())


out = None
basic_url = 'https://journals.ub.uni-heidelberg.de/index.php/germania/issue/archive/'
record_nr = 0
for page in range(1, 8):
    url = basic_url + str(page)
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
    list_elements = journal_soup.find_all('a', class_='title')
    issues = []
    for list_element in list_elements:
        time_str = arrow.now().format('YYMMDD')
        if list_element.text.split("(")[1].split(")")[0] > '1955':
            continue
        else:
            if list_element.text.split("(")[1].split(")")[0] not in issues:
                issues.append(list_element.text.split("(")[1].split(")")[0].replace("/", "-"))
                out = open('records/germania/volume_' + list_element.text.split("(")[1].split(")")[0].replace("/",
                                                                                                              "-") + '.mrc', 'wb')
            else:
                out = out
            url = list_element['href']
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:66.0)'
            values = {'name': 'Helena Nebel',
                      'location': 'Berlin',
                      'language': 'Python'}
            headers = {'User-Agent': user_agent}
            data = urllib.parse.urlencode(values)
            data = data.encode('ascii')
            req = urllib.request.Request(url, data, headers)
            with urllib.request.urlopen(req) as response:
                issue_page = response.read().decode('utf-8')
            issue_soup = BeautifulSoup(issue_page, 'html.parser')
            article_nr = 0
            for article in issue_soup.find_all('div', class_='obj_article_summary'):
                if not any(word in article.text for word in
                           ["Titelei", "Inhalt", "Vorwort", "Titel", "Literatur", "Widmung", "Beilage",
                            "Neuerscheinungen", "Besprechungen"]):
                    title = article.find('div', class_='title')
                    article_url = title.find('a')['href']
                    article_nr += 1
                    req = urllib.request.Request(article_url, data, headers)
                    with urllib.request.urlopen(req) as response:
                        issue_page = response.read().decode('utf-8')
                    article_soup = BeautifulSoup(issue_page, 'html.parser')
                    category = article_soup.find('div', class_="item issue").find_all('div', class_='sub_item')[1].find(
                        'div', class_='value').text.strip()
                    if category in ["Sonstiges", "Literatur"]:
                        continue
                    create_new_record(article_soup, out, category, url)
                    record_nr += 1
subject_table.close()