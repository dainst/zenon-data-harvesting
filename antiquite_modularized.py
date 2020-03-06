import urllib.parse
import urllib.request
import json
import write_error_to_logfile
from datetime import datetime
from find_sysnumbers_of_volumes import find_sysnumbers
from harvest_records import harvest_records


dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")

volumes_sysnumbers = find_sysnumbers('000594790')


def create_publication_dicts(last_item_harvested_in_last_session, *other):
    publication_dicts = []
    items_harvested = []
    try:
        current_year = int(dateTimeObj.strftime("%Y"))
        basic_url = 'https://api.crossref.org/journals/1724-2134/works?filter=type%3Ajournal-article,from-print-pub-date%3A' \
                    + str(current_year - 1) + '&cursor='
        next_cursor = '*'
        request_nr = 0
        while True:
            request_nr += 1
            req = urllib.request.Request(basic_url + next_cursor)
            with urllib.request.urlopen(req) as response:
                response = response.read()
            response = response.decode('utf-8')
            json_response = json.loads(response)
            next_cursor = json_response['message']['next-cursor'].replace('+', '%2B')
            if not json_response['message']['items']:
                break
            for item in json_response['message']['items']:
                year_of_publication = str(item['issued']['date-parts'][0][0])
                volume, issue = item['issue'].split('-')
                if year_of_publication not in volumes_sysnumbers:
                    write_error_to_logfile.comment('Artikel von Antiquité konnten teilweise nicht geharvestet werden, da keine übergeordnete Aufnahme für das Jahr '
                                                   + year_of_publication + ' existiert.')
                    write_error_to_logfile.comment('Bitte erstellen Sie eine neue übergeordnete Aufnahme für das Jahr ' + year_of_publication + '.')
                    break
                current_item = int(year_of_publication + volume + issue.zfill(2))
                if current_item > last_item_harvested_in_last_session:
                    if item['title'][0] not in ["Volume Table of Contents", "Volume Contents", "From the Editor", "Bibliography", "From the Guest Editors"]:
                        with open('publication_dict.json', 'r') as publication_dict_template:
                            publication_dict = json.load(publication_dict_template)
                        publication_dict['title_dict']['main_title'] = item['title'][0].split(': ', 1)[0] if len(item['title'][0].split(": ", 1)) == 2 else item['title'][0]
                        publication_dict['title_dict']['sub_title'] = item['title'][0].split(': ', 1)[1] if len(item['title'][0].split(": ", 1)) == 2 else ''
                        publication_dict['authors_list'] = [author['family'] + ', ' + author['given'] for author in item['author']]
                        publication_dict['html_links'] = [item['URL']]
                        publication_dict['issue'] = issue
                        publication_dict['doi'] = item['DOI']
                        publication_dict['LDR_06_07'] = 'ab'
                        publication_dict['do_detect_lang'] = True
                        publication_dict['default_language'] = 'fre'
                        publication_dict['fields_590'] = ['arom', '2020xhnxmefra']
                        publication_dict['original_cataloging_agency'] = 'Crossref'
                        publication_dict['publication_year'] = year_of_publication
                        publication_dict['publication_etc_statement']['publication'] = {'place': 'Rome', 'responsible': 'École Française de Rome', 'country_code': 'it '}
                        publication_dict['rdacontent'] = 'txt'
                        publication_dict['rdamedia'] = 'c'
                        publication_dict['rdacarrier'] = 'cr'
                        publication_dict['host_item'] = {'name': "Mélanges de l'École Française de Rome. Antiquité", 'sysnumber': volumes_sysnumbers[year_of_publication]}
                        publication_dict['host_item']['issn'] = '1724-2134'
                        publication_dict['volume'] = volume
                        publication_dict['field_006'] = 'm     o  d |      '
                        publication_dict['field_007'] = 'cr uuu   uu|uu'
                        publication_dict['field_008_18-34'] = 'fr p|o |||||   a|'
                        publication_dicts.append(publication_dict)
                        items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Antiquité geharvested werden.')
        items_harvested, publication_dicts = [], []
    return publication_dicts, items_harvested


def harvest(path):
    return_string = harvest_records(path, 'antiquite', 'Antiquité', create_publication_dicts)
    return return_string


if __name__ == '__main__':
    harvest_records('records/antiquite/', 'antiquite', 'Antiquité', create_publication_dicts)

# Valid filters for this route are: until-approved-date, has-assertion, from-print-pub-date,
# until-deposit-date, from-accepted-date, has-authenticated-orcid, from-created-date, relation.object,
# issn, until-online-pub-date, group-title, full-text.application, until-created-date, license.version,
# from-deposit-date, has-abstract, has-event, from-approved-date, funder, assertion-group,
# from-online-pub-date, from-issued-date, directory, content-domain, license.url, reference-visibility,
# from-index-date, full-text.version, full-text.type, until-posted-date, has-orcid, has-archive, type,
# is-update, until-event-start-date, update-type, from-pub-date, has-license, funder-doi-asserted-by,
# isbn, has-full-text, doi, orcid, has-content-domain, prefix, until-event-end-date, has-funder,
# award.funder, clinical-trial-number, member, has-domain-restriction, until-accepted-date,
# container-title, license.delay, from-posted-date, has-affiliation, from-update-date, has-award,
# until-print-pub-date, from-event-start-date, has-funder-doi, until-index-date, has-update,
# until-update-date, until-issued-date, until-pub-date, award.number, has-references, type-name,
# has-relation, alternative-id, archive, relation.type, updates, relation.object-type, category-name,
# has-clinical-trial-number, assertion, article-number, has-update-policy, from-event-end-date"
