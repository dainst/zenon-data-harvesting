from pymarc import MARCReader

filestring = 'records/world_prehistory/world_prehistory_12-Feb-2020'
count = 0
out = open('records/gnomon/gnomon_12-Feb-2020' + '_' + str(count) + '.mrc', 'wb')
print(filestring + '.mrc')
with open(filestring + '.mrc', 'rb') as file:
    new_reader = MARCReader(file)
    print(new_reader)
    print()
    for record in new_reader:
        if count % 25 == 0:
            out = open(filestring + '_' + str(count) + '.mrc', 'wb')
        out.write(record.as_marc21())
        count += 1