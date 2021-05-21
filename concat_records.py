from pymarc import MARCReader
import os


seen = []
dir_name = 'records/sidestone/'
filestring = 'sidestone_03_09.mrc'
count = 0
out = open(filestring, 'wb')
for file in os.listdir(dir_name):
    with open(dir_name + file, 'rb') as marc_file:
        new_reader = MARCReader(marc_file, force_utf8=True)
        for record in new_reader:
            if record['245']['a'] not in seen:
                seen.append(record['245']['a'])
                out.write(record.as_marc21())
                count += 1
            else:
                #print(record['245']['a'])
#print(count, 'Records wurden in der Datei gespeichert.')