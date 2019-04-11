import urllib.parse
import urllib.request

url = 'https://muse.jhu.edu/journal/399'
user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
values = {'name': 'Lisa Meier',
          'location': 'Tulsa',
          'language': 'Python' }
headers = {'User-Agent': user_agent}

data = urllib.parse.urlencode(values)
data = data.encode('ascii')
req = urllib.request.Request(url, data, headers)
with urllib.request.urlopen(req) as response:
    the_page = response.read()
the_page=the_page.decode('utf-8')

from bs4 import BeautifulSoup
soup=BeautifulSoup(the_page, 'html.parser')
liste=soup.find_all
list_elements=soup.find_all('li', class_='volume')
issues=[]
for list_element in list_elements:
    url = 'https://muse.jhu.edu' + str(list_element.span.a).split('"')[1]
    issue_name=str(list_element.span.a).split('"')[1][7:]
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
    values = {'name': 'Lisa Meier',
              'location': 'Tulsa',
              'language': 'Python' }
    headers = {'User-Agent': user_agent}

    data = urllib.parse.urlencode(values)
    data = data.encode('ascii')
    req = urllib.request.Request(url, data, headers)
    with urllib.request.urlopen(req) as response:
        the_page = response.read()
    the_page=the_page.decode('utf-8')
    with open(issue_name+'.html', 'w')as file:
        file.write(the_page)

#"/issue..." hinten anhängen, um alle Seiten zu finden. Daraus kann man dann dois machen.