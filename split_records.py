from pymarc import MARCReader

filestring = 'records/hsozkult/hsozkult_to_recent'
count = 0
out = open('records/hsozkult/hsozkult_to_recent/hsozkult_to_recent' + '_' + str(count) + '.mrc', 'wb')
print(filestring + '.mrc')
with open(filestring + '.mrc', 'rb') as file:
    new_reader = MARCReader(file)
    print(new_reader)
    print()
    for record in new_reader:
        if count % 25 == 0:
            out = open(filestring + str(count) + '.mrc', 'wb')
        out.write(record.as_marc21())
        count += 1