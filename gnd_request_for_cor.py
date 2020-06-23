import urllib.request
import json
import time
import write_error_to_logfile
import unidecode


def check_gnd_for_name(name_to_check: str):
    name_to_check = name_to_check.replace(' ', '+')
    name_to_check = unidecode.unidecode(name_to_check)
    search_url = 'https://lobid.org/gnd/search?q=%28preferredName%3A' + name_to_check + '+OR+variantName%3A' + name_to_check + '%29&size=1000&format=json'
    success = False
    trials = 0
    while not success:
        if trials >= 10:
            break
        try:
            req = urllib.request.Request(search_url)
            with urllib.request.urlopen(req) as response:
                json_response=response.read()
            json_response=json_response.decode('utf-8')
            json_response=json.loads(json_response)
            if json_response['totalItems'] > 0:
                member_nr = 0
                cor_nr = 0
                for member in json_response['member']:
                    member_nr += 1
                    if any(word in ['CorporateBody', 'TerritorialCorporateBodyOrAdministrativeUnit', 'ConferenceOrEvent', 'PlaceOrGeographicName'] for word in member['type']):
                        cor_nr += 1
                if cor_nr / member_nr > 0.5:
                    return True
            success=True
            return False
        except Exception as e:
            write_error_to_logfile.write(e)
            trials += 1
