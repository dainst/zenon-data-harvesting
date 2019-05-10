articles={'eng': ['the','a', 'an'], 'fre':['la','le','les','un', 'une', 'l\'', 'il'], 'spa':['el','lo','la','las','los',
    'uno' 'un', 'unos', 'unas', 'una'], 'ger':['das', 'der', 'ein', 'eine', 'die'], 'ita':['gli', 'i','le', 'la', 'l\'',
    'lo', 'il', 'gl\'', 'l']}
import re
from sickle import Sickle
from pymarc import Record, Field
from langdetect import detect
import language_codes
import json
import arrow

with open('last_harvesting_time.txt', 'r') as time_file:
    last_harvesting_time=time_file.read()

with open('eperiodica_journals.json', 'r') as journals:
    eperiodica_journals=json.load(journals)

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

def update_journal_titles(doi_list, eperiodica_journals):
    output="Bitte geben Sie Informationen für die Journals mit den folgenden PIDs an oder legen Sie gegebenenfalls Aufnahmen an:\n\n"
    output_per_journal=""
    pid_list=[]
    for doi in doi_list:
        if doi[13:20] not in pid_list:
            pid_list.append(doi[13:20])
            if doi[13:20] not in eperiodica_journals.keys():
                sickle2 = Sickle('https://www.e-periodica.ch/oai/dataprovider')
                content_list=sickle2.GetRecord(identifier=doi, metadataPrefix = 'oai_dc')
                content_list=list(content_list)
                output_per_journal+="PID: " + doi[13:20] + \
                        "\nInformationen zum Journal finden Sie auf der folgenden Seite unter dem Reiter \"Detailed Information\":\n"\
                        + 'https://doi.org/'+content_list[14][1][2][4:]+"\n\n"
                print(output, output_per_journal)
                print("Bitte geben Sie folgende Informationen zum Journal mit der PID "+ doi[13:20] + " an:\n")
                eperiodica_journals[doi[13:20]]={"SYS":input("Bitte geben Sie die Systemnummer des Journals an: "),
                                "TIT":input("\nBitte geben Sie den Titel des Journals an: ")}
    #hier Checks einbauen! (z.B. Kriterien für Systemnummern. Sind diese numerisch oder alphanumerisch? immer gleiche Länge?
    with open('eperiodica_journals.json', 'w') as journals:
        json.dump(eperiodica_journals, journals)

update_journal_titles(identify_dois(), eperiodica_journals)


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
                                      subfields = ['a', 'ANA', 'b', eperiodica_journals[journal_pid]['SYS'], 'l', 'DAI01',
                                                   'm', titles[0][1], 'n', eperiodica_journals[journal_pid]['TIT']+', '+
                                                  volume_nr+' ('+year_of_volume+')']))
        else:
            recent_record.add_field(Field(tag='LKR', indicators = [' ', ' '],
                                          subfields = ['a', 'ANA', 'b', eperiodica_journals[journal_pid]['SYS'], 'l', 'DAI01',
                                                       'm', titles[0][1], 'n', eperiodica_journals[journal_pid]['TIT']+', '+year_of_volume]))
        out.write(recent_record.as_marc21())
        article_number+=1
    print("Alle Records wurden erfolgreich erstellt.")
    print("Die Zeit des letzten Harvestings wurde auf ", last_harvesting_time, " aktualisiert")
time=arrow.now().format('YYMMDD')
create_records(identify_dois(), time)

#from-parameter einbauen!!!
# wie soll das genau funktionieren? soll das Dictionary mit den ZS immer per Hand geupdatet werden?
# Oder soll ich ein Programm schreiben, dass ausgibt, ob auf der Seite neue Zeitschriften dazugekommen sind?