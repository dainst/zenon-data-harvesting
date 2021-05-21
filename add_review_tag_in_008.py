import csv
import urllib.request
from pymarc import MARCReader

nr = 0
out = open('records/reviews/substitution_records.mrc', 'wb')
with open('Rezensionen-reportresults.csv', "r") as record_table:
    reader = csv.reader(record_table, delimiter=';')
    row_nr = 0
    for row in reader:
        row_nr += 1
        if row_nr > 1:
            record_id = row[0]
            try:
                webfile = urllib.request.urlopen("https://zenon.dainst.org/Record/" + record_id + "/Export?style=MARC")
                new_reader = MARCReader(webfile, force_utf8=True)
                for file in new_reader:
                    out.write(file.as_marc21())
                    nr += 1
            except Exception as e:
                #print(e)