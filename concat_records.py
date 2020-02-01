from pymarc import MARCReader
import os

page_range = '300-400'

dir_name = 'records/hsozkult/hsozkult_' + page_range + '/'
filestring = 'records/hsozkult/all_' + page_range + '.mrc'
count = 0
out = open(filestring, 'wb')
for file in os.listdir(dir_name):
    with open(dir_name + file, 'rb') as marc_file:
        print(marc_file)
        new_reader = MARCReader(marc_file)
        for record in new_reader:
            out.write(record.as_marc21())
            count += 1
print(count, 'Records wurden in der Datei gespeichert.')