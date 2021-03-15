import urllib.request
import json
from pymarc import MARCReader, Field


starting_page_nr = 22800 # hier immer ändern! erledigt: bis 22800
nr = 0
out = open('records/add_zeros/substitution_records.mrc', 'wb')
page_nr = 0
empty_page = False
while not empty_page:
    print(page_nr)
    if page_nr == 7200:
        break
    url = u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0%5B%5D=*&illustration=-1&page=' + str(starting_page_nr + page_nr)
    page_nr += 1
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        response = response.read()
    response = response.decode('utf-8')
    json_response = json.loads(response)
    if 'records' not in json_response:
        empty_page = True
        print('empty page')
        continue
    for record in json_response['records']:
        try:
            webfile = urllib.request.urlopen(
                "https://zenon.dainst.org/Record/" + record['id'] + "/Export?style=MARC")
            new_reader = MARCReader(webfile, force_utf8=True)
            for file in new_reader:
                if nr % 25 == 0:
                    out = open('records/add_zeros/substitution_records_' + str(starting_page_nr*20 + nr) + '.mrc', 'wb')
                substitute = False
                for field in file.get_fields('773'):
                    if field['w']:
                        if len(field['w']) != 9:
                            field['w'] = field['w'].zfill(9)
                            substitute = True
                            print(file)
                for field in file.get_fields('776'):
                    if field['w']:
                        if len(field['w']) != 9:
                            field['w'] = field['w'].zfill(9)
                            substitute = True
                            print(file)
                for field in file.get_fields('787'):
                    if field['w']:
                        if len(field['w']) != 9:
                            field['w'] = field['w'].zfill(9)
                            substitute = True
                            print(file)
                if substitute:
                    file.add_field(Field(tag='590', indicators=[' ', ' '], subfields=['a', '2021xhnxupdated']))
                    out.write(file.as_marc21())
                    nr += 1
        except:
            print('not found:', record['id'])

