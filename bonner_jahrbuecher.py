import urllib.parse, urllib.request
import csv
import urllib.parse, urllib.request
from pymarc import Record, Field
import arrow
import language_codes
from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer, word_tokenize
import ast
import spacy
from scipy import spatial
import unicodedata
from nltk.corpus import stopwords
import itertools
import re
from langdetect import detect
from nameparser import HumanName
from datetime import datetime
import json

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")

with open('records/bjb/bjb_logfile.json', 'r') as log_file:
    log_dict = json.load(log_file)
    last_item_harvested_in_last_session = log_dict['last_issue_harvested']
    print('Letztes geharvestetes Heft von Bonner Jahrbücher:', last_item_harvested_in_last_session)

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

titles_author_not_detected = {"Neue deutsche Ausgrabungen. Unter Mitwirkung von Verschiedenen, herausgegeben von Gerhart Rodenwaldt":{"title": "Neue deutsche Ausgrabungen", "editors": "Gerhart Rodenwaldt", "rev_auth": None},
                              "S. N. Miller M. A. The Roman Fort at Old Kilpatrick on the Antonine Wall, being an Account of Excavations conducted on Behalf of the Glasgow Archaeological Society":{"title": "The Roman Fort at Old Kilpatrick on the Antonine Wall, being an Account of Excavations conducted on Behalf of the Glasgow Archaeological Society", "editors": None, "rev_auth": "S. N. Miller"},
                              "Friedrich Hertlein, Oskar Paret und Peter Gössler: Die Römer in Württemberg":{"title": "Die Römer in Württemberg", "editors": None, "rev_auth": "Friedrich Hertlein und Oskar Paret und Peter Gössler"},
                              "Dr. Friedrich Wagner: Die Römer in Bayern":{"title": "Die Römer in Bayern", "editors": None, "rev_auth": "Friedrich Wagner"},
                              "K. H. Jacob-Friesen, Grundfragen der Urgeschichtsforschung":{"title": "Grundfragen der Urgeschichtsforschung", "editors": None, "rev_auth": "K. H. Jacob-Friesen"},
                              "Bibliotheca Philologica Classica. Beiblatt zum Jahresbericht über die Fortschritte der klassischen Altertumswissenscha[f]t":{"title": "Bibliotheca Philologica Classica. Beiblatt zum Jahresbericht über die Fortschritte der klassischen Altertumswissenscha[f]t", "editors": None, "rev_auth": None},
                              "Dr. Max Bernhart, Münzkunde der römischen Kaiserzeit. I. Band. Bibliographischer Wegweiser":{"title": "Münzkunde der römischen Kaiserzeit. I. Band. Bibliographischer Wegweiser", "editors": None, "rev_auth": "Max Bernhart"},
                              "Bibliotheca Philologica Classica. Beiblatt zum Jahresberichte über die Fortschritte der klassischen Altertumswissenschaft. Bd. 45, herausg. von Franz Zimmermann":{"title": "Bibliotheca Philologica Classica. Beiblatt zum Jahresberichte über die Fortschritte der klassischen Altertumswissenschaft. Bd. 45", "editors": "Franz Zimmermann", "rev_auth": None},
                              "Germania Romana. Ein Bilderatlas herausgegeben von der Römisch-germanischen Kommission des Deutschen archaeologischen Instituts":{"title": "Germania Romana. Ein Bilderatlas", "editors": "Römisch-germanische Kommission des Deutschen Archaeologischen Instituts", "rev_auth": None},
                              "Derselbe, Die Nerosäule des Samus und Severus. Nachtrag zu Quilling, Die Juppitersäule usw.":{"title": "Die Nerosäule des Samus und Severus", "editors": None, "rev_auth": "F. Quilling"},
                              "Derselbe, Die Juppiter-Votivsäule der Mainzer Canabarii":{"title": "Die Juppiter-Votivsäule der Mainzer Canabarii", "editors": None, "rev_auth": "F. Quilling"},
                              "Der Reihengräberfund von Gammertingen, auf höchsten Befehl S. K. H. des Fürsten von Hohenzollern beschrieben von J. W. Gröbbels":{"title": "Der Reihengräberfund von Gammertingen", "editors": None, "rev_auth": "J. W. Gröbbels"},
                              "Dr. Franz Cramer, Rheinische Ortsnamen aus vorrömischer und römischer Zeit":{"title": "Rheinische Ortsnamen aus vorrömischer und römischer Zeit", "editors": None, "rev_auth": "Franz Cramer"},
                              "Artur Engel et Raymond Serrure, Traité de numismatique moderne et contemporaine":{"title": "Traité de numismatique moderne et contemporaine", "editors": None, "rev_auth": "Artur Engel et Raymond Serrure"},
                              "Hengstenberg, Hermann, Das ehemalige Herzogtum Berg und seine nächste Umgebung, Elberfeld 1897":{"title": "Das ehemalige Herzogtum Berg und seine nächste Umgebung", "editors": None, "rev_auth": "Hermann Hengstenberg"},
                              "Die kölnischen Stadtpläne des Arnold Mercator und des Cornelius ab Egmont von 1571 und 1642":{"title": "Die kölnischen Stadtpläne des Arnold Mercator und des Cornelius ab Egmont von 1571 und 1642", "editors": None, "rev_auth": None},
                              "Paul Clemen (Hrsg.), Die Kunstdenkmäler der Rheinprovinz. Dritter Band. III. Die Kunstdenkmäler des Kreises Neuss":{"title": "Die Kunstdenkmäler der Rheinprovinz. Dritter Band. III. Die Kunstdenkmäler des Kreises Neuss", "editors": "Paul Clemen", "rev_auth": ""},
                              "Neue Heidelberger Jahrbücher, Heidelberg 1895":{"title": "Neue Heidelberger Jahrbücher", "editors": None, "rev_auth": None},
                              "Christian Mehlis, Studien zur ältesten geschichte der Rheinlande, Neustadt a. d. H. 1895":{"title": "Studien zur ältesten geschichte der Rheinlande", "editors": None, "rev_auth": "Christian Mehlis"},
                              "Dr. Mathaeus Much, die Kupferzeit in Europa und ihr Verhältniss zur Kultur der Indogermanen":{"title": "Die Kupferzeit in Europa und ihr Verhältniss zur Kultur der Indogermanen", "editors": None, "rev_auth": "Mathaeus Much"},
                              "Ed. Piette, L'époque éburnéene et les races humaines de la période glyptique":{"title": "L'époque éburnéene et les races humaines de la période glyptique", "editors": None, "rev_auth": "Ed. Piette"},
                              "Edm. Meyer, Untersuchungen über die Schlacht im Teutoburger Walde":{"title": "Untersuchungen über die Schlacht im Teutoburger Walde", "editors": None, "rev_auth": "Edm. Meyer"},
                              "Edictum Diocletiani de pretiis rerum venalium. Edidit Th. Mommsen. — Der Maximaltarif des Diocletian. Erläutert von H. Blümner":{"title": "Edictum Diocletiani de pretiis rerum venalium", "editors": "Th. Mommsen", "rev_auth": None},
                              "Repertorium Hymnologicum, Catalogue des chants, hymnes, proses, séquences, tropes en usage dans l’église latine depuis les origines jusqu’à nos jours par le chanoine Ulisse Chevalier":{"title": "Repertorium Hymnologicum, Catalogue des chants, hymnes, proses, séquences, tropes en usage dans l’église latine depuis les origines jusqu’à nos jours par le chanoine Ulisse Chevalier", "editors": None, "rev_auth": None},
                              "„Neue Heidelberger Jahrbücher“ III, 1. Heidelberg. G. Köster":{"title": "Neue Heidelberger Jahrbücher III, 1", "editors": None, "rev_auth": None},
                              "A. Engel et R. Serrure: Traite de numismatique du moyen-âge. Tome deuxième, depuis la fin de l’époque Carolingien ne jusqu’à l’apparition du gros d’argent":{"title": "Traite de numismatique du moyen-âge. Tome deuxième, depuis la fin de l’époque Carolingien ne jusqu’à l’apparition du gros d’argent", "editors": None, "rev_auth": "A. Engel et R. Serrure"},
                              "Prof. Dr. Otto Kohl: Ueber die Verwendung römischer Münzen beim Unterricht":{"title": "Ueber die Verwendung römischer Münzen beim Unterricht", "editors": None, "rev_auth": "Otto Kohl"},
                              "Moderne Geschichtsforscher. I. J. Lulves, Die gegenwärtigen Geschichtsbestrebungen in Aachen":{"title": "Die gegenwärtigen Geschichtsbestrebungen in Aachen", "editors": None, "rev_auth": "I. J. Lulves"},
                              "Meteorologische Volksbücher. Ein Beitrag zur Geschichte der Meteorologie und zur Kulturgeschichte":{"title": "Meteorologische Volksbücher. Ein Beitrag zur Geschichte der Meteorologie und zur Kulturgeschichte", "editors": None, "rev_auth": None},
                              "Beiträge zur Geschichte der Stadt Greifswald, begonnen von Dr. C. Gesterding, fortges. von Dr. Th. Pyl. Dritte Fortsetzung. Die niederrheinische und westphälische Einwanderung in Rügisch-Pommern, sowie die Anlage und Benennung der Stadt Greifswald":{"title": "Beiträge zur Geschichte der Stadt Greifswald. Dritte Fortsetzung. Die niederrheinische und westphälische Einwanderung in Rügisch-Pommern, sowie die Anlage und Benennung der Stadt Greifswald", "editors": None, "rev_auth": "Th. Pyl."},
                              "A. Engel et R. Serrure: Traité de numismatique du moyen-âge. Tome premier, depuis la chute de l’empire Romain d’occident jusqu’à la fin de l’époque carolingienne":{"title": "Traité de numismatique du moyen-âge. Tome premier, depuis la chute de l’empire Romain d’occident jusqu’à la fin de l’époque carolingienne", "editors": None, "rev_auth": "A. Engel et R. Serrure"},
                              "Leemans, Grieksche Opschriften uit Klein-Azië in den laatsten Tijd voor het Rijks-Museum van Oudheden te Leiden aangewonnen":{"title": "Grieksche Opschriften uit Klein-Azië in den laatsten Tijd voor het Rijks-Museum van Oudheden te Leiden aangewonnen", "editors": None, "rev_auth": "Leemans"},
                              "Dr. Otto Adalbert Hoffmann, der Steinsaal des Alterthumsmuseums zu Metz":{"title": "Der Steinsaal des Alterthumsmuseums zu Metz", "editors": None, "rev_auth": "Otto Adalbert Hoffmann"},
                              "K. Bissinger: Funde römischer Münzen im Grossherzogthum Baden":{"title": "Funde römischer Münzen im Grossherzogthum Baden", "editors": None, "rev_auth": "K. Bissinger"},
                              "Prof. H. Landois und Dr. B. Vormann, Westfälische Todtenbäume und Baumsargmenschen":{"title": "Westfälische Todtenbäume und Baumsargmenschen", "editors": None, "rev_auth": "H. Landois und B. Vormann"},
                              "W. M. Flinders Petrie, Hawara, Biahmu and Arsinoe":{"title": "Petrie, Hawara, Biahmu and Arsinoe", "editors": None, "rev_auth": "W. M. Flinders"},
                              "Grempler, Der Fund von Sackrau":{"title": "Der Fund von Sackrau", "editors": None, "rev_auth": "Grempler"},
                              "Samwer, Die Grenzpolizei des römischen Reichs":{"title": "Die Grenzpolizei des römischen Reichs", "editors": None, "rev_auth": "Samwer"},
                              "Hermann Schiller, Geschichte der römischen Kaiserzeit, zweiter Band. Von Diokletian bis zum Tode Theodosius des Grossen":{"title": "Geschichte der römischen Kaiserzeit, zweiter Band. Von Diokletian bis zum Tode Theodosius des Grossen", "editors": None, "rev_auth": "Hermann Schiller"},
                              "Feu Paul-Emile Giraud et Ulysse Chevalier, Le mystère des trois doms. Lyo":{"title": "Le mystère des trois doms. Lyo", "editors": None, "rev_auth": "Paul-Emile Giraud et Ulysse Chevalier"},
                              "A. B. Meyer. Gurina im Obergailthale, Kärnthen":{"title": "Gurina im Obergailthale, Kärnthen", "editors": None, "rev_auth": "A. B. Meyer"},
                              "Heinr. Hub. Koch, Divisionspfarrer in Frankfurt a. M. Ueber Handel und Industrie in den Rheinlanden, mit besonderer Berücksichtigung der Gegend von Eschweiler":{"title": "Divisionspfarrer in Frankfurt a. M. Ueber Handel und Industrie in den Rheinlanden, mit besonderer Berücksichtigung der Gegend von Eschweiler", "editors": None, "rev_auth": "Heinr. Hub. Koch"},
                              "Dr. Ludwig Beck. Die Geschichte des Eisens in technischer und kulturhistorischer Beziehung":{"title": "Die Geschichte des Eisens in technischer und kulturhistorischer Beziehung", "editors": None, "rev_auth": "Ludwig Beck"},
                              "Die Baugeschichte der Kirche des h. Victor zu Xanten, von Stephan Beissel, Freiburg i. B.1883":{"title": "Die Baugeschichte der Kirche des h. Victor zu Xanten", "editors": None, "rev_auth": "Stephan Beissel"},
                              "F. v. Apell, Major im Ingenieurkorps, Argentoratum, ein Beitrag zur Ortsgeschichte von Strassburg i. E.":{"title": "Major im Ingenieurkorps, Argentoratum, ein Beitrag zur Ortsgeschichte von Strassburg i. E.", "editors": None, "rev_auth": "F. v. Apell"},
                              "Die Holzbaukunst. Vorträge in der Berliner Bauakademie, gehalten von Dr. Paul Lehfeldt":{"title": "Die Holzbaukunst. Vorträge in der Berliner Bauakademie, gehalten von Dr. Paul Lehfeldt", "editors": None, "rev_auth": None},
                              "Die Neuerbürg an der Wied und ihre ersten Besitzer. Zugleich ein Versuch zur Lösung der Frage: Wer war Heinrich von Ofterdingen? Von H. J. Hermes":{"title": "Die Neuerbürg an der Wied und ihre ersten Besitzer. Zugleich ein Versuch zur Lösung der Frage: Wer war Heinrich von Ofterdingen?", "editors": None, "rev_auth":  "H. J. Hermes"},
                              "Vorgeschichte Roms von Johann Gustav Cuno. I. Theil. Die Kelten":{"title": "Vorgeschichte Roms. I. Theil. Die Kelten", "editors": None, "rev_auth": "von Johann Gustav Cuno"},
                              "Dr. Heinrich Schliemann, Mykenae. Bericht über meine Forschungen und Entdeckungen in Mykenae und Tiryns":{"title": "Mykenae. Bericht über meine Forschungen und Entdeckungen in Mykenae und Tiryns", "editors": None, "rev_auth": "Heinrich Schliemann"},
                              "Al. Ecker, Ueber prähistorische Kunst, 1877":{"title": "Ueber prähistorische Kunst", "editors": None, "rev_auth": "Al. Ecker"},
                              "Étude sur les peuples primitifs de la Russie. Les Mériens, par le comte A. Ouvaroff, trad. par F. Malaqué":{"title": "Étude sur les peuples primitifs de la Russie. Les Mériens", "editors": None, "rev_auth": "A. Ouvaroff"},
                              "E. de Meester de Ravestein: A propos de certaines classifications préhistoriques":{"title": "A propos de certaines classifications préhistoriques", "editors": None, "rev_auth": "E. de Meester de Ravestein"},
                              "Brambach Wilhelm, Corpus Inscriptionum Rhenanarum, 1867":{"title": "Corpus Inscriptionum Rhenanarum", "editors": None, "rev_auth": "Wilhelm Brambach"},
                              "P. Cornelii Taciti opera. Ex vetustissimis codicibus a se denuo collatis, glossis seclusis, lacunis retectis, mendis correctis, recensuit Franciscus Ritter":{"title": "P. Cornelii Taciti opera", "editors": None, "rev_auth": "Franciscus Ritter"},
                              "Die alte Martinskirche in Bonn und ihre Zerstörung von Prof. Dr. Hermann Hüffer":{"title": "Die alte Martinskirche in Bonn und ihre Zerstörung", "editors": None, "rev_auth": "Hermann Hüffer"},
                              "Beschrijving van de voorwerpen van Germaanschen, Germaansch-Celtischen en Romeinschen oorsprong en van lateren tijd, J. V. W. Krul van Sfrompwijk en Dr. J. H. A. Scheers":{"title": "Beschrijving van de voorwerpen van Germaanschen, Germaansch-Celtischen en Romeinschen oorsprong en van lateren tijd", "editors": None, "rev_auth": "J. V. W. Krul van Sfrompwijk und Dr. J. H. A. Scheers"},
                              "Bulletin de la Société d'Archéologie et d'histoire de la de la Moselle":{"title": "Bulletin de la Société d'Archéologie et d'histoire de la de la Moselle", "editors": None, "rev_auth": None},
                              "Trier und seine Alterthümer. Ein Wegweiser für Einheimische und Fremde, von P. Chr. Sternberg, Trier":{"title": "Trier und seine Alterthümer. Ein Wegweiser für Einheimische und Fremde", "editors": None, "rev_auth": "P. Chr. Sternberg"},
                              "Inscriptiones Germaniae primae et Germaniae secundae, bearbeitet von Hofrath Dr. Steiner, Seligenstadt 1851":{"title": "Inscriptiones Germaniae primae et Germaniae secundae", "editors": None, "rev_auth": "Steiner"},
                              "Der Feldzug des Germanicus an der Weser im Jahre 16. nach Chr. Geb, von E. von Wietersheim, Leipzig 1850":{"title": "Der Feldzug des Germanicus an der Weser im Jahre 16. nach Chr. Geb", "editors": None, "rev_auth": "E. von Wietersheim"},
                              "De Wal, De Moedergodinnen.":{"title": "De Moedergodinnen.", "editors": None, "rev_auth": "Jan de Wal"},
                              "1. I. Steininger Geschichte der Trevirer unter der Herrschaft der Römer. Mit einer Karte und einem Abschnitte der Tabula Peutingeriana":{"title": "Geschichte der Trevirer unter der Herrschaft der Römer. Mit einer Karte und einem Abschnitte der Tabula Peutingeriana", "editors": None, "rev_auth": "I. Steininger"},
                              "2. G. Schneemann Rerum Trevericarum commentatio I. Programm des Gymnasiums zu Trier vom Jahre 1844":{"title": "Rerum Trevericarum commentatio I. Programm des Gymnasiums zu Trier vom Jahre 1844", "editors": None, "rev_auth": "G. Schneemann "},
                              "Mittheilungen der Gesellschaft für vaterländische Alterthümer in Basel. I. Die römischen Inschriften des Kantons Basel von Dr. K. L. Roth. Druck und Verlag von J. J. Mast. 1843., 4°. max. 4 Bogen":{"title": "Mittheilungen der Gesellschaft für vaterländische Alterthümer in Basel. I. Die römischen Inschriften des Kantons Basel", "editors": None, "rev_auth": "K. L. Roth"},
                              "Geschichte der Stadt Mainz von K. A. Schaab, D. U. I. und Vizepräsident des Kreisgerichts zu Mainz. Erster Band. Mainz 1841. In Commission bei F. Kupferberg. 8°. 594 S.":{"title": "Geschichte der Stadt Mainz. Erster Band", "editors": None, "rev_auth": "K. A. Schaab"},
                              "Jahresberichte und Archiv des historischen Vereins von und für Oberbayern. Von 1838 bis 1842. 16 Hefte":{"title": "Jahresberichte und Archiv des historischen Vereins von und für Oberbayern", "editors": None, "rev_auth": None},
                              "Bormann ( Pfarrer in Daleiden), Geschichte der Ardennen. 2 Theile. Trier 1841, 1842.":{"title": "Geschichte der Ardennen", "editors": None, "rev_auth": "Bormann"},
                              "Van Asch van Wyck (Ihr. Mr. H. M. A. J. Statsrad etc.) Geschiedkundige beschouwing van het oude handelsverkeer der stadt Utrecht van de vroegste tijden af tot aan de XIV. eeuw. Utrecht 1828 bis 1842. 3 Hefte.":{"title": "Geschiedkundige beschouwing van het oude handelsverkeer der stadt Utrecht van de vroegste tijden af tot aan de XIV. eeuw.", "editors": None, "rev_auth": "Van Asch van Wyck"},
                              "Der Mayengau oder das Mayenfeld, nicht Mayfeld. Eine historisch geographische Untersuchung von L. von Ledebur. Berlin 1842":{"title": "Der Mayengau oder das Mayenfeld, nicht Mayfeld. Eine historisch geographische Untersuchung", "editors": None, "rev_auth": "L. von Ledebur"},
                              "Die ehernen Streitkeile zumal in Deutschland. Eine historisch-archäologische Monographie von Dr. Heinrich Schreiber, d.Z. Prorector an der Albert-Ludwigs-Universität zu Freiburg im Breisgau. Freiburg 1842. 4. 92 S. und 2 Tafeln":{"title": "Die ehernen Streitkeile zumal in Deutschland. Eine historisch-archäologische Monographie", "editors": None, "rev_auth": "Heinrich Schreiber"},
                              "Dr. Heinrich Schreiber die Feen in Europa":{"title": "Die Feen in Europa", "editors": None, "rev_auth": "Heinrich Schreiber"},
                              'Ergebnisse der neuesten Ausgrabungen römischer Alterthümer in und bei Mainz. Zusammengestellt von Dr. H. M. Malten. Besonders abgedruckt aus dem zweiten Bande von 1842 der "Bibliothek der neuesten Weltkunde". Mainz 1842, 45 S. 8':{"title": "Ergebnisse der neuesten Ausgrabungen römischer Alterthümer in und bei Mainz", "editors": None, "rev_auth": "H. M. Malten"},
                                "Hauptmann, Carl, Grundsätze der römischen Erdvermessung": {"title": "Grundsätze der römischen Erdvermessung", "rev_auth": "Carl Hauptmann", "editors": None},
                              "P. Cesare A. de Cara, Gli Hyksôs o Re Pastori di Egitto": {"title": "Gli Hyksôs o Re Pastori di Egitto", "rev_auth": "P. Cesare und A. de Cara", "editors": None},
                              "Naue, Dr. Julius. Die Hügelgräber zwischen Ammer- und Staffelsee": {"title": "Die Hügelgräber zwischen Ammer- und Staffelsee", "rev_auth": "Julius Naue", "editors": None},
                              "Die römischen Denksteine des grossherzoglichen Antiquariums in Mannheim von Prof. Ferd. Haug, Konstanz": {"title": "Die römischen Denksteine des grossherzoglichen Antiquariums in Mannheim", "rev_auth": "Ferd. Haug", "editors": None}
                              }


out = open('records/bjb/bjb_' + timestampStr + '.mrc', 'wb')
basic_url = 'https://journals.ub.uni-heidelberg.de/index.php/bjb/issue/archive/'
record_nr = 0
empty_page = False
page = 0
while not empty_page:
    page += 1
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
    if not list_elements:
        empty_page = True
    for list_element in list_elements:
        time_str = arrow.now().format('YYMMDD')
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
        volume_title = issue_soup.find('title').text
        if "Beilage" not in volume_title:
            volume_nr = volume_title.split(":")[0].replace("Bd. ", "").strip().replace(")", "").split(" (")[0]
        else:
            continue
        volume_name = volume_title.split(": ")[1].split("|")[0].strip()
        if len(re.findall(r'\d{4}', volume_title))>0:
            volume_year = re.findall(r'\d{4}', volume_title)[-1]
        else:
            volume_year = volume_title.split("(")[1].split(")")[0]
        article_nr = 0
        for article in issue_soup.find_all('div', class_='obj_article_summary'):
            title = article.find('div', class_='title')
            article_url = title.find('a')['href']
            article_nr += 1
            req = urllib.request.Request(article_url, data, headers)
            with urllib.request.urlopen(req) as response:
                issue_page = response.read().decode('utf-8')
            article_soup = BeautifulSoup(issue_page, 'html.parser')
            category = article_soup.find('div', class_="item issue").find_all('div', class_='sub_item')[1].find(
                'div', class_='value').text.strip()
            if category not in ['Titel', 'Inhalt', 'Verbesserungen', 'Vorwort/Widmung', 'Abkürzungen']:
                # swagger_find_reviewed_article(recent_record, title, rev_auths, print_title, year_of_reviewed_title)
                # swagger_search_review(search_title, search_authors, print_title, recent_record, year_of_reviewed_title, title)

                abstract_text = ""
                doi = None
                pdf = None
                pages = None
                review = False
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
                title = title.replace("...", "")
                year = article_soup.find('meta', attrs={'name': 'citation_date'})['content']
                if category in ['Bildbeilage', 'Register', 'Miszellen', 'Chronik', 'Vereinsangelegenheiten_Statuten', 'Berichte', 'Jahresberichte']:
                    title = title+volume_name + ', ' +volume_nr + ' (' + year + ')'
                print_title = title
                if article_soup.find('meta', attrs={'name': 'citation_doi'}) != None:
                    doi = 'https://doi.org/' + article_soup.find('meta', attrs={'name': 'citation_doi'})['content']
                    recent_record.add_field(Field(tag='024', indicators=['7', ' '], subfields=['a', doi, '2', 'doi']))
                abstract = article_soup.find('meta', attrs={'name': 'citation_abstract_html_url'})['content']
                if article_soup.find('meta', attrs={'name':'DC.Description'})!= None:
                    abstract_text = article_soup.find('meta', attrs={'name':'DC.Description'})['content']
                if article_soup.find('meta', attrs={'name': 'citation_pdf_url'}) != None:
                    pdf = article_soup.find('meta', attrs={'name': 'citation_pdf_url'})['content']
                if article_soup.find('meta', attrs={'name': 'DC.Identifier.pageNumber'}) != None:
                    pages = article_soup.find('meta', attrs={'name': 'DC.Identifier.pageNumber'})['content']
                author_nr = 0
                for author in authors:
                    if author != "Die Redaktion":
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
                recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', '2019xhnxbjb']))
                recent_record.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', 'online publication']))
                recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'cr  uuu    a uuuuu'))
                if category in ["Litteratur", "Besprechungen"]:
                    if title not in ["Nachtrag zur Anzeige der in der Hermes’schen Schrift 'Die Neuerburg an der Wied' angeregten Frage: Wer war Heinrich von Ofterdingen?",
                                     "Rheinische Bibliographie", "Litteratur", "Bemerkungen zu der bei Gall in Trier erschienenen Schrift des Dr. Jacob Schneider", "Bemerkungen über das römische Baudenkmal zu Fliessem, in Bezug auf die, im IV. Hefte dieser Jahrbücher, erschienene Recension"]:
                        for title in title.split(" / "):
                            review = True
                            rev_auth = None
                            editors = None
                            year_of_reviewed_title = ""
                            if title in titles_author_not_detected:
                                rev_auth = titles_author_not_detected[title]['rev_auth']
                                editors = titles_author_not_detected[title]['editors']
                                if re.findall(r'\d{4}', title)!=[]:
                                    for item in re.findall(r'\d{4}', title):
                                        if 1840<int(item)<1900:
                                            if title.find(item)>(len(title)/4)*3:
                                                pattern = r'[,.;:\?][^,.:;]*?'+item
                                                if re.findall(pattern, title)!=[]:
                                                    if title.find(re.findall(pattern, title)[-1])>(len(title)/3)*2:
                                                        year_of_reviewed_title = item
                                title = titles_author_not_detected[title]['title']
                            else:
                                if re.findall(r'\d{4}', title)!=[]:
                                    for item in re.findall(r'\d{4}', title):
                                        if 1840<int(item)<1900:
                                            if title.find(item)>(len(title)/4)*3:
                                                pattern = r'[,.;:\?][^,.:;]*?'+item
                                                if re.findall(pattern, title)!=[]:
                                                    if title.find(re.findall(pattern, title)[-1])>(len(title)/3)*2:
                                                        year_of_reviewed_title = item
                                                        split_text = re.findall(pattern, title)[-1]
                                                        title = title.split(split_text)[0]
                                for editorship_word in ["Hrsg, von ", "Hrsg. von ", "Herausgegeben von ", "hrsg. von ", "herausgegeben von ", "herausg. von ", "Herausgegeb. von ", "; edd. ",
                                                        " bearbeitet von ", "Aus den Quellen bearbeitet von ", "mit Text von ", "Mit Einleitung, Commentar und zwei Karten versehen von ",
                                                        "Den Herrn H. Meyer und H. Koechly gewidmet von ", "Zusammengestellt von ",
                                                        "Aufgenommen und gezeichnet v. ", "Zusammengestellt von ", "Beschrieben und durch XXVI Tafeln erläutert von ", "Erläutert von ", "pubblicata da ", "collegit ",
                                                        "publié par ", "; edd. ", " Mit Einleitung, Commentar und zwei Karten versehen von "]:
                                    if editorship_word in title:
                                        title, editors = title.split(editorship_word)
                                        title = title.strip().strip(", ").strip(". ")
                                        rev_auth = None
                                for responsibility_word in ["Beschrieben von ", "Aus den Quellen bearbeitet von ", "mit Text von ", "Mit Einleitung, Commentar und zwei Karten versehen von ",
                                                            "Den Herrn H. Meyer und H. Koechly gewidmet von ",
                                                            "Aufgenommen und gezeichnet v. ", "Beschrieben und durch XXVI Tafeln erläutert von ", "dessinées par ", "dessinée par ", "eröffnet und beschrieben von ",
                                                            "von Gymnasialdirector ", "Bijdrage van ", ", by ", " di ", "instruxit ", " scripsit ", "Bijdrage van ", ", étude par "]:
                                    if responsibility_word in title:
                                        title, rev_auth = title.rsplit(responsibility_word, 1)
                                        title = title.strip().strip(", ").strip(". ")
                                if re.findall(r'[,.] {1,2}[Vv]on ', title)!=[]:
                                    title, responsible_person=title.split(re.findall(r'[,.] {1,2}[Vv]on ', title)[-1])
                                    rev_auth = responsible_person
                                if rev_auth is None:
                                    if re.findall(r' {1,2}von ', title)!=[]:
                                        if title.find(re.findall(r' {1,2}von ', title)[-1])>(len(title)/3)*2:
                                            title, responsible_person=title.rsplit(re.findall(r' {1,2}von ', title)[-1], 1)
                                            rev_auth = responsible_person
                                if " par " in title:
                                    title, responsible_person=title.split(" par ")[:2]
                                    rev_auth = responsible_person
                                if " pel " in title:
                                    title, responsible_person=title.split(" pel ")
                                    rev_auth = responsible_person
                                title = title.strip()
                                lang = detect(title)
                                if rev_auth == None:
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
                                                    title = title.split(word.text, 1)[1]
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
                                                            title = title.replace(rev_auth, "")
                                                            for coordination in [" und ", " et ", " and "]:
                                                                if title.find(coordination)==0:
                                                                    title = title.strip(coordination)
                                                                    tagged_rest_of_title = nlp(title)
                                                                    for ent in tagged_rest_of_title.ents:
                                                                        if ent.label_ == "PER":
                                                                            if title.startswith(ent.text) == True:
                                                                                if len(ent.text.split()) > 1:
                                                                                    rev_auth += coordination
                                                                                    rev_auth += ent.text
                                                                                    title = title.replace(ent.text, "")
                                                                        break
                                                                break
                                                            punctuation = title.replace(rev_auth, "")[0]
                                                            if punctuation != " ":
                                                                title=title[1:]
                                                            break
                                                            #hier Problem, Satzzeichen werden nicht entfernt
                                                break
                                    else:
                                        nlp = nlp_xx
                                        tagged_sentence = nlp(title)
                                        for ent in tagged_sentence.ents:
                                            if ent.label_ == "PER":
                                                if title.startswith(ent.text) == True:
                                                    if len(ent.text.split()) > 1:
                                                        rev_auth = ent.text
                                                        title = title.replace(rev_auth, "")
                                                        for coordination in [" und ", " et ", " and "]:
                                                            if title.find(coordination)==0:
                                                                title = title.strip(coordination)
                                                                tagged_rest_of_title = nlp(title)
                                                                for ent in tagged_rest_of_title.ents:
                                                                    if ent.label_ == "PER":
                                                                        if title.startswith(ent.text) == True:
                                                                            if len(ent.text.split()) > 1:
                                                                                rev_auth += coordination
                                                                                rev_auth += ent.text
                                                                                title = title.replace(ent.text, "")
                                                                        break
                                                                break
                                                        punctuation = title.replace(rev_auth, "")[0]
                                                        if punctuation != " ":
                                                            title=title[1:]
                                                        break
                                                break
                            rev_auths = []
                            if rev_auth != None:
                                print_authors = ""
                                if any(coordination in rev_auth for coordination in [" und ", " et ", " and "]):
                                    for coordination in [" und ", " et ", " and "]:
                                        if coordination in rev_auth:
                                            for auth in rev_auth.split(coordination):
                                                name=HumanName(auth)
                                                print_authors += (name.last+", "+name.first+" "+name.middle).strip() + ", "
                                                rev_auths.append(name.last)
                                            break
                                else:
                                    name=HumanName(rev_auth)
                                    print_authors += (name.last+", "+name.first+" "+name.middle).strip() + ", "
                                    rev_auths.append(name.last)
                                print_title = "[Rez.zu:]" + print_authors.strip(", ") + ": " + title.strip(",").strip(".").strip()
                            elif editors != None:
                                title.strip()
                                print_editors = ""
                                if any(coordination in editors for coordination in [" und ", " et ", " and "]):
                                    for coordination in [" und ", " et ", " and "]:
                                        if coordination in editors:
                                            for edit in editors.split(coordination):
                                                name=HumanName(edit)
                                                print_editors += (name.last+", "+name.first+" "+name.middle).strip() + ", "
                                            break
                                elif editors == "Römisch-germanische Kommission des Deutschen Archaeologischen Instituts":
                                    print_editors = "Römisch-germanische Kommission des Deutschen Archaeologischen Instituts"
                                else:
                                    name=HumanName(editors)
                                    print_editors += (name.last+", "+name.first+" "+name.middle).strip() + ", "
                                print_title = "[Rez.zu:]" + print_editors.strip(", ") + "(Hrsg.): " + title.strip()
                            else:
                                print_title = "[Rez.zu:]" + title.strip()
                            title = title.strip()
                            #if not any(word in title for word in ["Neue Heidelberger Jahrbücher", "Die Kunstdenkmäler der Rheinprovinz"]):
                                #swagger_find_reviewed_article(recent_record, title, rev_auths, print_title, year_of_reviewed_title)
                #nonfiling_characters = determine_nonfiling_characters(recent_record, title, year, review)
                #create_245_and_246(recent_record, print_title, nonfiling_characters, author_nr)
                producers = {'138': ['Darmstadt', "L.C. Wittich'sche Hofbuchdruckerei"],
                             '106': ['Bonn', "A. Marcus und E. Weber's"],
                             '84': ['Bonn', 'Adolph Marcus'],
                             '3': ['Bonn', 'A. Marcus'],
                             '1': ['Cöln', 'F.C. Eisen']}
                publishers = {'1949': ['Kevelaer Rhld.', 'Butzon & Bercker'],
                              '1948': ['Düsseldorf', 'L. Schwann'],
                              '1933': ['Darmstadt', '[Verein von Altertumsfreunden im Rheinlande]'],
                              '1932': ['Bonn ; Darmstadt', 'Gebr. Scheuer'],
                              '1928': ['Bonn', 'Universitätsbuchdruckerei Gebr. Scheur'],
                              '1927': ['Köln', 'Albert Ahn'],
                              '1921': ['Bonn', "A. Marcus und E. Weber's"],
                              '1840': ['Bonn', '[Verein von Altertumsfreunden im Rheinlande]']}
                years_published_in = list(publishers.keys())
                years_published_in.sort(reverse=True)
                years_produced_in = [int(producer_key) for producer_key in list(producers.keys())]
                years_produced_in.sort(reverse=True)
                for key in years_published_in:
                    if year >= key:
                        recent_record.add_field(Field(tag='264', indicators=['3', '1'],
                                                      subfields=['a', publishers[key][0], 'b', publishers[key][1], 'c', year]))
                        if publishers[key][1] in ['[Verein von Altertumsfreunden im Rheinlande]']:
                            for year_produced_in in years_produced_in:
                                if int(volume_nr.split("/")[0])>= year_produced_in:
                                    recent_record.add_field(Field(tag='264', indicators=['3', '0'],
                                                                  subfields=['a', producers[str(year_produced_in)][0], 'b', producers[str(year_produced_in)][1]]))
                                    break
                        break
                if (doi != None) and (abstract_text.strip() != "-"):
                    recent_record.add_field(Field(tag='856', indicators=['4', '2'],
                                                  subfields=['z', 'Abstract', 'u', abstract]))
                if pdf != None:
                    recent_record.add_field(Field(tag='856', indicators=['4', '0'],
                                                  subfields=['z', 'application/pdf', 'u', pdf]))
                recent_record.add_field(Field(tag='856', indicators=['4', '2'],
                                              subfields=['z', 'Table of Contents', 'u', url]))
                if review:
                    recent_record.add_field(Field(tag='LKR', indicators=[' ', ' '],
                                                  subfields=['a', 'ANA', 'b', '001578364', 'l', 'DAI01',
                                                             'm', print_title, 'n', '[Rez.in]: ' + volume_name + ', ' +
                                                             volume_nr + ' (' + year + ')']))
                else:
                    recent_record.add_field(Field(tag='LKR', indicators=[' ', ' '],
                                                  subfields=['a', 'ANA', 'b', '001578364', 'l', 'DAI01',
                                                             'm', print_title, 'n', volume_name + ', ' +
                                                             volume_nr + ' (' + year + ')']))
                if pages != None:
                    recent_record.add_field(Field(tag='300', indicators=[' ', ' '], subfields=['a', 'pp. ' + pages]))
                language = language_codes.resolve(article_soup.find('meta', attrs={'name': 'DC.Language'})['content'])
                data_008 = str(time_str) + 's' + year + '    ' + 'gw ' + ' |   oo    |    |' + language + ' d'

                record_nr += 1
# Lücke zwischen 1933 und 1986 beachten!!!
# bis wann harvesten?
# zurückgestellt, weil erst 3 Jahre nach Erscheinung open access zugänglich; nur für ältere Volumes oder wie Vorgehen?
print(record_nr)