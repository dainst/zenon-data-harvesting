import create_new_record
from datetime import datetime
import json
import write_error_to_logfile
import os

dateTimeObj = datetime.now()
timestampStr = dateTimeObj.strftime("%d-%b-%Y")


def harvest_records(path: str, short_name: str, real_name: str, create_publication_dicts,
                    publisher=None, publication_place=None, default_language=None, time_interval=None, host_item_sysnumber=None,
                    field_008_18_34=None):
    return_string = ''
    try:
        try:
            with open('records/' + short_name + '/' + short_name + '_logfile.json', 'r') as log_file:
                log_dict = json.load(log_file)
                last_item_harvested_in_last_session = log_dict['last_item_harvested']
                write_error_to_logfile.comment('Letztes geharvestetes Heft von ' + real_name + ': ' + str(last_item_harvested_in_last_session))
            out = open(path + short_name + '_' + timestampStr + '.mrc', 'wb')
            pub_nr = 0
            publication_dicts, issues_harvested = create_publication_dicts(last_item_harvested_in_last_session, short_name, real_name, publisher, publication_place, default_language, time_interval,
                                                                           host_item_sysnumber, field_008_18_34)
            for publication_dict in publication_dicts:
                if create_new_record.check_publication_dict_for_completeness_and_validity(publication_dict):
                    created = create_new_record.create_new_record(out, publication_dict)
                    pub_nr += created
                else:
                    pub_nr = 0
                    break
        except Exception as e:
            write_error_to_logfile.write(e)
            pub_nr = 0
            issues_harvested = []
        if not pub_nr:
            if os.path.exists(path + short_name + '_' + timestampStr + '.mrc'):
                os.remove(path + short_name + '_' + timestampStr + '.mrc')
        write_error_to_logfile.comment('Es wurden ' + str(pub_nr) + ' neue Records für ' + real_name + ' erstellt.')
        return_string += 'Es wurden ' + str(pub_nr) + ' neue Records für ' + real_name + ' erstellt.\n'
        if issues_harvested and pub_nr:
            with open('records/' + short_name + '/' + short_name + '_logfile.json', 'w') as log_file:
                log_dict = {"last_item_harvested": max(issues_harvested)}
                json.dump(log_dict, log_file)
                write_error_to_logfile.comment('Log-File wurde auf ' + str(max(issues_harvested)) + ' geupdated.')
        else:
            if os.path.exists(path + short_name + '_' + timestampStr + '.mrc'):
                os.remove(path + short_name + '_' + timestampStr + '.mrc')
    except Exception as e:
        write_error_to_logfile.write(e)
        write_error_to_logfile.comment('Es konnten keine Records für' + real_name + ' erstellt werden.')
        return_string += 'Es konnten keine Records für' + real_name + ' erstellt werden.'
    return return_string
