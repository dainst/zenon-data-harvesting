import urllib.request
import json

def find_sysnumbers(sysnumber_host_item):
    volumes_sysnumbers = {}
    page_nr = 0
    empty_page = False
    while not empty_page:
        page_nr += 1
        volumes_url = 'https://zenon.dainst.org/api/v1/search?lookfor=' + sysnumber_host_item + \
                      '&type=ParentID&page=' + str(page_nr)
        req = urllib.request.Request(volumes_url)
        with urllib.request.urlopen(req) as response:
            response = response.read()
        response = response.decode('utf-8')
        json_response = json.loads(response)
        if 'records' not in json_response:
            empty_page = True
            continue
        for result in json_response['records']:
            for date in result['publicationDates']:
                volumes_sysnumbers[date] = result['id']
    return volumes_sysnumbers