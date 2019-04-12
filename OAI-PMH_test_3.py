journal_titles={"akb-001": {"SYS":"001563083", "TIT":"Archäologie im Kanton Bern"} , "akb-002": {"SYS":"001563084", "TIT":"Archäologie Bern"} ,
"ars-001": {"SYS":"001563085","TIT":"Archäologie der Schweiz"} , "ars-002": {"SYS":"001563086", "TIT":"Archäologie Schweiz : Mitteilungsblatt von Archäologie Schweiz "} ,
"bat-001": {"SYS":"001563087", "TIT":"Bollettino dell'Associazione archeologica ticinese"} , "bpa-001": {"SYS":"001563088", "TIT":"Bulletin de l'Association Pro Aventico"} ,
"bzg-001": {"SYS":"001563089", "TIT":"Beiträge zur vaterländischen Geschichte"} , "bzg-002": {"SYS":"001563090", "TIT":"Basler Zeitschrift für Geschichte und Altertumskunde"} ,
"caf-001": {"SYS":"001563091", "TIT":"Chronique archéologique"} , "caf-002": {"SYS":"001563092", "TIT":"Cahiers d'archéologie fribourgeoise"} ,
"gen-001": {"SYS":"001563093", "TIT":"Genava"}, "gpv-001": {"SYS":"001563094", "TIT":"Jahresbericht / Gesellschaft Pro Vindonissa"} ,
"has-001": {"SYS":"001563095", "TIT":"Hefte des Archäologischen Seminars der Universität Bern"} , "jak-001": {"SYS":"001563096", "TIT":"Jahresberichte aus Augst und Kaiseraugst"} ,
"jas-001": {"SYS":"001563097", "TIT":"Jahresbericht der Schweizerischen Gesellschaft für Urgeschichte"} , "jas-002": {"SYS":"001563098", "TIT":"Jahrbuch der Schweizerischen Gesellschaft für Urgeschichte"} ,
"jas-003": {"SYS":"001563099", "TIT":"Jahrbuch der Schweizerischen Gesellschaft für Ur- und Frühgeschichte"} , "jas-004": {"SYS":"001563100", "TIT":"Jahrbuch Archäologie Schweiz"} ,
"mhl-001": {"SYS":"001563101", "TIT":"Museum Helveticum"} , "oac-001": {"SYS":"001563102", "TIT":"Entretiens sur l'Antiquité classique"} ,
"rhv-001": {"SYS":"001563103", "TIT":"Revue historique vaudoise"} , "smb-001": {"SYS":"001563104", "TIT":"Schweizer Münzblätter"} ,
"snr-001": {"SYS":"001563105", "TIT":"Bulletin de la Société suisse de Numismatique"} , "snr-002": {"SYS":"001563106", "TIT":"Revue suisse de numismatique"} ,
"snr-003": {"SYS":"001563107", "TIT":"Schweizerische numismatische Rundschau"} , "tug-001": {"SYS":"001563108", "TIT":"Tugium"} ,
"zak-001": {"SYS":"001563109", "TIT":"Anzeiger für schweizerische Alterthumskunde"} , "zak-002": {"SYS":"001563110", "TIT":"Anzeiger für schweizerische Altertumskunde : Neue Folge"} ,
"zak-003": {"SYS":"001563111", "TIT":"Zeitschrift für schweizerische Archäologie und Kunstgeschichte"}}
articles={'eng': ['the','a', 'an'], 'fre':['la','le','les','un', 'une', 'l\'', 'il'], 'spa':['el','lo','la','las','los',
    'uno' 'un', 'unos', 'unas', 'una'], 'ger':['das', 'der', 'ein', 'eine', 'die'], 'ita':['gli', 'i','le', 'la', 'l\'',
    'lo', 'il', 'gl\'', 'l']}
import re
from sickle import Sickle
from pymarc import Record, Field
from langdetect import detect
import arrow
import language_codes

def identify_dois():
    sickle = Sickle('https://www.e-periodica.ch/oai/dataprovider')
    records_930 = sickle.ListIdentifiers(metadataPrefix='oai_dc', set='ddc:930')
    doi_list=[]
    item_number=0
    for record in records_930:
        if item_number>5:
            break
        record_splitted=re.split('identifier',str(record))
        doi=record_splitted[1][1:-2]
        doi_list.append(doi)
        item_number+=1
    return doi_list

def create_records(doi_list, time):
    journal_pid=""
    article_number=0
    out=".mrc"
    for doi in doi_list:
        sickle2 = Sickle('https://www.e-periodica.ch/oai/dataprovider')
        content_list=sickle2.GetRecord(identifier=doi, metadataPrefix = 'oai_dc')
        content_list=list(content_list)
        if journal_pid!=content_list[14][1][0][43:50]:
            journal_pid=content_list[14][1][0][43:50]
            out=open('records/'+str(journal_pid+'_'+'0'+'.mrc'), 'wb')
            article_number=0
        if article_number%20==0 and article_number>=20:
            out=open('records/'+str(journal_pid+'_'+str(int(article_number/20))+'.mrc'), 'wb')
        recent_record=Record(force_utf8=True)
        title=content_list[0][1][0]
        titles=[]
        languages=[]
        parallel_title_nr=0
        for parallel_title in title.split(" = "):
            titles.append([])
            try:
                languages.append(language_codes.resolve(detect(parallel_title)))
            except:
                languages.append('   ')
            part_of_title_nr=0
            parallel_title=(parallel_title.strip(" : ").strip(" = "))
            for part_of_title in parallel_title.split(" : ", 1):
                if part_of_title_nr==0:
                    titles[parallel_title_nr].append('a')
                else:
                    titles[parallel_title_nr].append('b')
                titles[parallel_title_nr].append(part_of_title)
                part_of_title_nr+=1
            parallel_title_nr+=1
        recent_record.leader = recent_record.leader[:5] + 'nmb a       uu ' + recent_record.leader[20:]
        recent_record.add_field(Field(tag='040', indicators = [' ', ' '], subfields = ['a', 'eperiodica', 'd', 'DE-2553']))
        recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'online publication']))
        recent_record.add_field(Field(tag='590', indicators = [' ', ' '], subfields = ['a', 'arom']))
        recent_record.add_field(Field(tag='336', indicators = [' ', ' '], subfields = ['a', 'text', 'b', 'txt', '2', 'rdacontent']))
        recent_record.add_field(Field(tag='042', indicators=[' ', ' '], subfields=['a', 'dc']))
        recent_record.add_field(Field(tag='006', indicators=None, subfields=None, data=u'm        u        '))
        recent_record.add_field(Field(tag='007', indicators=None, subfields=None, data=u'cuuuuu   uuauu'))
        recent_record.add_field(Field(tag='024', indicators = ['7', ' '], subfields = ['a', content_list[14][1][2][4:], '2', 'doi']))
        data_008=str(time)+'s'+ content_list[6][1][0][:5] + '    ' + 'sz' + '                  ' + languages[0] +' d'
        recent_record.add_field(Field(tag='008', indicators=None, subfields=None, data=data_008))
        creator_number=0
        for creator in content_list[1][1]:
            if creator not in [None,'[s.n.]']:
                if creator_number==0:
                    recent_record.add_field(Field(tag='100', indicators = ['1', ' '], subfields = ['a', creator]))
                    creator_number=1
                else:
                    recent_record.add_field(Field(tag='700', indicators = ['1', ' '], subfields = ['a', creator]))
        parallel_title_nr=0
        for parallel_title in titles:
            nonfiling_characters=0
            if languages[parallel_title_nr]!='   ':
                recent_record.add_field(Field(tag='041', indicators = ['1', ' '], subfields = ['a', languages[parallel_title_nr]]))
            if languages[parallel_title_nr] in articles.keys():
                first_word=(parallel_title[1].split()[0]).lower()
                if first_word in articles[languages[parallel_title_nr]]:
                    nonfiling_characters=str(len(first_word)+1)
            if parallel_title_nr==0:
                recent_record.add_field(Field(tag='245', indicators = [str(creator_number), nonfiling_characters], subfields = parallel_title))
            else:
                print(titles)
                recent_record.add_field(Field(tag='246', indicators = [str(creator_number), nonfiling_characters], subfields = parallel_title))
            parallel_title_nr+=1
        if content_list[4][1][0] not in [None,'[s.n.]'] and content_list:
            recent_record.add_field(Field(tag='260', indicators = [' ', ' '],
                                          subfields = ['b', content_list[4][1][0], 'c', content_list[6][1][0][:5]]))
        recent_record.add_field(Field(tag='856', indicators = ['4', '1'],
                                subfields = ['z', 'Table of Contents', 'u', content_list[14][1][0]]))
        recent_record.add_field(Field(tag='856', indicators = ['4', '1'],
                                      subfields = ['z', 'application/pdf', 'u', content_list[14][1][1]]))
        recent_record.add_field(Field(tag='856', indicators = ['4', '1'],
                                      subfields = ['z', 'Table of Contents', 'u', 'https://doi.org/'+content_list[14][1][2][4:]]))
        volume_nr=(content_list[14][1][0][51:].split("::")[0]).split(":")[1]
        year_of_volume=(content_list[14][1][0][51:].split("::")[0]).split(":")[0]
        if volume_nr!='0':
            recent_record.add_field(Field(tag='LKR', indicators = [' ', ' '],
                                      subfields = ['a', 'ANA', 'b', journal_titles[journal_pid]['SYS'], 'l', 'DAI01',
                                                   'm', titles[0][1], 'n', journal_titles[journal_pid]['TIT']+', '+
                                                  volume_nr+' ('+year_of_volume+')']))
        else:
            recent_record.add_field(Field(tag='LKR', indicators = [' ', ' '],
                                          subfields = ['a', 'ANA', 'b', journal_titles[journal_pid]['SYS'], 'l', 'DAI01',
                                                       'm', titles[0][1], 'n', journal_titles[journal_pid]['TIT']+', '+year_of_volume]))
        out.write(recent_record.as_marc21())
        article_number+=1
    print("Alle Records wurden erfolgreich erstellt.")
time=arrow.now().format('YYMMDD')
create_records(identify_dois(), time)

#from-parameter einbauen!!!
# wie soll das genau funktionieren? soll das Dictionary mit den ZS immer per Hand geupdatet werden?
# Oder soll ich ein Programm schreiben, dass ausgibt, ob auf der Seite neue Zeitschriften dazugekommen sind?
#https://www.loc.gov/marc/dccross.html Erklärung mapping dublin core auf MARC21
#Erklärung zu MARC: http://www.loc.gov/marc/umb/ http://www.loc.gov/marc/marcdocz.html