import re
from sickle import Sickle
import json
from _datetime import datetime
import write_error_to_logfile
from harvest_records import harvest_records


def create_publication_dicts(last_item_harvested_in_last_session, journal_pid_underscore, host_item_name, publisher, publication_place, default_language, time_interval, host_item_sysnumber,
                             field_008_18_34):
    publication_dicts = []
    items_harvested = []
    try:
        journal_pid = journal_pid_underscore.replace('_', '-')
        dateTimeObj = datetime.now()
        last_year_of_harvesting = int(dateTimeObj.strftime("%Y")) - time_interval
        date_string = str(last_item_harvested_in_last_session)[:4] + '-01-01'
        sickle = Sickle('https://www.e-periodica.ch/oai/dataprovider')
        records_930 = sickle.ListIdentifiers(**{'metadataPrefix': 'oai_dc', 'set': 'ddc:930', 'from': date_string})
        doi_list = []
        start_of_journal = False
        for record in records_930:
            record_splitted = re.split('identifier', str(record))
            doi = record_splitted[1][1:-2]
            if doi[13:20] == journal_pid and int(re.findall(r'(\d{4}):\d{1,3}::', doi)[0]) <= last_year_of_harvesting:
                start_of_journal = True
                doi_list.append(doi)
            if doi[13:20] != journal_pid and start_of_journal:
                break
        for doi in doi_list:
            sickle2 = Sickle('https://www.e-periodica.ch/oai/dataprovider')
            content_list = list(sickle2.GetRecord(identifier=doi, metadataPrefix='oai_dc'))
            year = content_list[6][1][0][:5]
            volume_year, volume_nr = re.findall(r'(\d{4}):(\d{1,3})::', content_list[14][1][0][51:])[0]
            current_item = int(volume_year + volume_nr.zfill(3))
            if current_item > last_item_harvested_in_last_session:
                with open('publication_dict.json', 'r') as publication_dict_template:
                    publication_dict = json.load(publication_dict_template)
                parallel_title_nr = 0
                for parallel_title in content_list[0][1][0].split(" = "):
                    if parallel_title_nr == 0:
                        if ' : ' in parallel_title:
                            publication_dict['title_dict']['main_title'], publication_dict['title_dict']['sub_title'] = parallel_title.split(' : ', 1)
                        else:
                            publication_dict['title_dict']['main_title'] = parallel_title
                    else:
                        publication_dict['parallel_titles'].append(parallel_title)
                    parallel_title_nr += 1
                publication_dict['authors_list'] = [creator for creator in content_list[1][1] if creator not in [None, '[s.n.]']]
                publication_dict['table_of_contents_link'] = content_list[14][1][0]
                publication_dict['pdf_links'].append(content_list[14][1][1])
                publication_dict['doi'] = content_list[14][1][2][4:]
                publication_dict['default_language'] = default_language
                publication_dict['do_detect_lang'] = True
                publication_dict['fields_590'] = ['Online publication', 'arom', '2020xhnx' + journal_pid.replace('-', '')]
                publication_dict['original_cataloging_agency'] = 'eperiodica'
                publication_dict['publication_year'] = year
                publication_dict['publication_etc_statement']['publication'] = {'place': publication_place, 'responsible': publisher, 'country_code': 'sz '}
                publication_dict['rdacontent'] = 'txt'
                publication_dict['rdamedia'] = 'c'
                publication_dict['rdacarrier'] = 'cr'
                publication_dict['host_item']['name'] = host_item_name
                publication_dict['host_item']['sysnumber'] = host_item_sysnumber
                publication_dict['volume'] = volume_nr if int(volume_nr) != 0 else ''
                publication_dict['volume_year'] = volume_year
                publication_dict['retro_digitization_info'] = {'place_of_publisher': '', 'publisher': '', 'date_published_online': ''}
                publication_dict['terms_of_use_and_reproduction'] = {'terms_note': 'Die auf der Plattform E-Periodica veröffentlichten Dokumente stehen für nicht-kommerzielle Zwecke in Lehre und '
                                                                                   'Forschung sowie für die private Nutzung frei zur Verfügung.', 'use_and_reproduction_rights': '',
                                                                     'terms_link': 'https://www.e-periodica.ch/digbib/about3'}
                publication_dict['LDR_06_07'] = 'ab'
                publication_dict['field_006'] = 'm     o  d |      '
                publication_dict['field_007'] = 'cr uuu   uu|uu'
                publication_dict['field_008_18-34'] = field_008_18_34
                publication_dict['additional_fields'].append({'tag': '042', 'indicators': [' ', ' '], 'subfields': ['a', 'dc'], 'data': ''})
                publication_dicts.append(publication_dict)
                items_harvested.append(current_item)
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Artikel für Aegyptiaca geharvested werden.')
    return publication_dicts, items_harvested


def harvest_eperiodica(path, journal_pid_underscore, host_item_name, create_publication_dicts, publisher, publication_place, default_language,
                       time_interval, host_item_sysnumber, field_008_18_34):
    return_string = harvest_records(path, journal_pid_underscore, host_item_name,  create_publication_dicts, publisher, publication_place, default_language,
                                    time_interval, host_item_sysnumber, field_008_18_34)
    return return_string


if __name__ == '__main__':
    harvest_eperiodica('records/bat_001/', 'bat_001', 'Bollettino dell’Associazione Archeologica Ticinese', create_publication_dicts, 'Associazione Archeologica Ticinese', 'Lugano', 'ita', 3, '001543081',  'ar p o||||||   a|')
    harvest_eperiodica('records/snr_003/', 'snr_003', 'Schweizerische numismatische Rundschau', create_publication_dicts, 'Schweizerische Numismatische Gesellschaft', 'Bern', 'ger', 3, '001570578', 'ar p o||||||   a|')
    harvest_eperiodica('records/akb_002/', 'akb_002', 'Archäologie Bern', create_publication_dicts, 'Archäologischer Dienst des Kantons Bern', 'Bern', 'ger', 2, '000855529', 'ar p o||||||   a|')
    # welche weiteren Publikationen?
