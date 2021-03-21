import urllib.request
import csv
from pymarc import MARCReader, Field
from urllib.error import HTTPError
import write_error_to_logfile

other_problems = []
nr = 0
out = open('records/check_links/substitution_records.mrc', 'wb')
with open('856-reportresults.csv', "r") as record_table:
    reader = csv.reader(record_table, delimiter=';')
    row_nr = 0
    for row in reader:
        row_nr += 1
        if row_nr > 1:
            record_id = row[0]
            invalid_link = False
            for identifier in row[2].split():
                if identifier[0] in ['h', 'w']:
                    write_error_to_logfile.write(record_id)
                    if identifier[0:3] == 'www':
                        identifier = 'http://' + identifier
                    try:
                        webfile = urllib.request.urlopen(identifier)
                    except HTTPError as err:
                        if err.code == 404:
                            webfile = urllib.request.urlopen("https://zenon.dainst.org/Record/" + record_id + "/Export?style=MARC")
                            new_reader = MARCReader(webfile, force_utf8=True)
                            for file in new_reader:
                                out.write(file.as_marc21())
                                nr += 1
                    except Exception as e:
                        write_error_to_logfile.write(e)
                        write_error_to_logfile.comment('invalid but not 404 ' + identifier)
                        other_problems.append(record_id)

write_error_to_logfile.comment(other_problems)
print(row_nr)
print(nr)
