import urllib.request
import json
from pymarc import MARCReader

out = open('records/add_zeros/substitution_records.mrc', 'wb')
page_nr = 0
empty_page = False
while not empty_page:
    url = u'https://zenon.dainst.org/api/v1/search?join=AND&lookfor0%5B%5D=*&illustration=-1&page=' + str(page_nr)
    page_nr += 1
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        response = response.read()
    response = response.decode('utf-8')
    json_response = json.loads(response)
    if 'records' not in json_response:
        empty_page = True
        continue
    for record in json_response['records']:
        try:
            webfile = urllib.request.urlopen(
                "https://zenon.dainst.org/Record/" + record['id'] + "/Export?style=MARC")
            new_reader = MARCReader(webfile, force_utf8=True)
            for file in new_reader:
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
                    out.write(file.as_marc21())
        except:
            print('not found:', record['id'])

