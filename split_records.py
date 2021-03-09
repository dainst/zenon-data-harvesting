from pymarc import MARCReader
import os
import re

filestring = 'all_lotti'


for filestring in os.listdir('gelehrtenbriefe_marc'):
    count = 0
    lotto_nr = re.findall('\d{2}', filestring)[0]
    out = open('g_splitted/gelehrtenbriefe_' + str(count) + '.mrc', 'wb')
    print(filestring + '.mrc')
    with open('gelehrtenbriefe_marc/' + filestring, 'rb') as file:
        new_reader = MARCReader(file)
        print(new_reader)
        print()
        for record in new_reader:
            print(record)
            if count % 50 == 0:
                out = open('g_splitted/gelehrtenbriefe_' + lotto_nr + '_' + str(count) + '.mrc', 'wb')
            out.write(record.as_marc21())
            count += 1