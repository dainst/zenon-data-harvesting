import urllib.request
from bs4 import BeautifulSoup
import re

download_url = 'https://biblio.ebaf.edu/cgi-bin/koha/opac-downloadcart.pl?bib_list='
volumes_url = 'https://biblio.ebaf.edu/cgi-bin/koha/opac-downloadcart.pl?bib_list='
for file in ['bm.html', 'bm2.html']:
    with open(file, 'r') as new_page:
        journal_soup = BeautifulSoup(new_page, 'html.parser')
        numbers = [re.findall(r'\d+$', url)[0] for url in [a['href'] for a in journal_soup.find_all('a', class_='title')]]
        for number in numbers:
            volumes_url += number + '/'
            url = 'https://biblio.ebaf.edu/cgi-bin/koha/opac-search.pl?op=do_search&idx=po&q=' + number
            # url = 'https://biblio.ebaf.edu/cgi-bin/koha/opac-search.pl?op=do_search&idx=po&q=94685'
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                journal_page = response.read()
            journal_page = journal_page.decode('utf-8')
            journal_soup = BeautifulSoup(journal_page, 'html.parser')
            print([re.findall(r'\d+$', url)[0] for url in [tag['href'] for tag in journal_soup.find_all('a', class_='title') if 'biblionumber' in tag['href']]])
            for new_number in [re.findall(r'\d+$', url)[0] for url in [tag['href'] for tag in journal_soup.find_all('a', class_='title') if 'biblionumber' in tag['href']]]:
                download_url += new_number + '/'


print(volumes_url)
print(download_url)