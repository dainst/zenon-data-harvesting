import urllib.request
import re
from pymarc import MARCReader
import json
import find_existing_doublets
import write_error_to_logfile


page = 0
empty_page = False
while not empty_page:
    page += 1
    try:
        print(page)
        url = u'https://zenon.dainst.org/api/v1/search?type=AllFields&sort=relevance&page='+str(page)+'&limit=100&prettyPrint=false&lng=de'
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            journal_page = response.read()
        json_response=journal_page.decode('utf-8')
        json_response=json.loads(json_response)
        if 'records' not in json_response:
            empty_page = True
            continue
        for result in json_response['records']:
            webFile = urllib.request.urlopen("https://zenon.dainst.org/Record/"+result['id']+"/Export?style=MARC")
            new_reader = MARCReader(webFile)
            all_results = [result['id']]
            try:
                for file in new_reader:
                    if 'b' in file['245']:
                        title = file['245']['a'] + ' ' + file['245']['b']
                    else:
                        title = file['245']['a']
                    authors = [author_field['a'].split(', ')[0] for author_field in file.get_fields('100', '700')]
                    if file.get_fields('260', '264'):
                        year = [min([int(year) for year in re.findall(r'\d{4}', field)]) for field in [field['c'] for field in file.get_fields('260', '264') if field['c']] if '©' not in field and re.findall(r'\d{4}', field)]
                    else:
                        year = None
                    default_lang = 'en'
                    possible_host_items = [field['b'] for field in file.get_fields('995') if field['a']=='ANA']
                    with open('publication_dict.json', 'r') as publication_dict_template:
                        publication_dict = json.load(publication_dict_template)
                    e_resource = False
                    publication_dict['LDR_06_07'] = file.leader[6:8]
                    if file['337']:
                        publication_dict['rdamedia'] = str(file['337']['b'])
                    if file['338']:
                        publication_dict['rdacarrier'] = str(file['338']['b'])
                    if file['006']:
                        publication_dict['field_006'] = file['006'].data
                        if str(file['006'].data)[0] == 'm':
                            publication_dict['rdamedia'] = 'c'
                    if file['007']:
                        publication_dict['field_007'] = file['007'].data
                        if str(file['007'])[0:2] == 'cr':
                            publication_dict['rdacarrier'] = 'cr'
                    for field in file.get_fields('856'):
                        if 'online' in str(field['z']).lower():
                            publication_dict['pdf_links'].append(str(field['u']))
                    if file['300']:
                        if 'online' in str(file['300']['a']).lower():
                            publication_dict['rdacarrier'] = 'cr'
                            publication_dict['rdamedia'] = 'c'
                    if file['533']:
                        if ('online' in str(file['533']['a']).lower()):
                            publication_dict['rdacarrier'] = 'cr'
                            publication_dict['rdamedia'] = 'c'
                    if file['590']:
                        if [str(field['a']).lower() for field in file.get_fields('590') if 'online' in str(field['a']) or 'ebook' in str(field['a'])]:
                            publication_dict['rdacarrier'] = 'cr'
                            publication_dict['rdamedia'] = 'c'
                    if file['245']['c']:
                        publication_dict['title_dict']['responsibility_statement'] = file['245']['c']
                    if year:
                        all_results, additional_physical_form_entrys = find_existing_doublets.find(title, authors, year[0], default_lang, possible_host_items, publication_dict)
                        # if result['id'] not in all_results:
                            # print('eigener Datensatz nicht gefunden', result['id'], all_results)
                        while result['id'] in all_results:
                            all_results.remove(result['id'])
                        if len(all_results)>=1:
                            print(result['id'], all_results)
                    # else:
                        # print('Jahreszahl fehlt:', result['id'])

            except Exception as e:
                write_error_to_logfile.write(e)
                write_error_to_logfile.comment(result['id'])

    except Exception as e:
        write_error_to_logfile.write(e)

