from crossref.restful import Works, Prefixes, Journals, Etiquette

works = Works()

# Sample
works.agency('10.1590/0102-311x00133115')

# {'DOI': '10.1590/0102-311x00133115',
 # 'agency': {'id': 'crossref', 'label': 'CrossRef'}}

for item in works.sample(2):
    print(item['title'])

# ['On the Origin of the Color-Magnitude Relation in the Virgo Cluster']
# ['Biopsychosocial Wellbeing among Women with Gynaecological Cancer']

# Query

w1 = works.query(bibliographic='zika', author='johannes', publisher_name='Wiley-Blackwell')

for item in w1:
    print(item['title'])

# ['Inactivation and removal of Zika virus during manufacture of plasma-derived medicinal products']
# ['Harmonization of nucleic acid testing for Zika virus: development of the 1st\n World Health Organization International Standard']

# Doi

works.doi('10.1590/0102-311x00133115')
'''
{'DOI': '10.1590/0102-311x00133115',
 'ISSN': ['0102-311X'],
 'URL': 'http://dx.doi.org/10.1590/0102-311x00133115',
 'alternative-id': ['S0102-311X2016001107002'],
 'author': [{'affiliation': [{'name': 'Surin Rajabhat University,  Thailand'}],
             'family': 'Wiwanitki',
             'given': 'Viroj'}],
 'container-title': ['Cadernos de Saúde Pública'],
 'content-domain': {'crossmark-restriction': False, 'domain': []},
 'created': {'date-parts': [[2016, 12, 7]],
             'date-time': '2016-12-07T21:52:08Z',
             'timestamp': 1481147528000},
 'deposited': {'date-parts': [[2017, 5, 24]],
               'date-time': '2017-05-24T01:57:26Z',
               'timestamp': 1495591046000},
 'indexed': {'date-parts': [[2017, 5, 24]],
             'date-time': '2017-05-24T22:39:11Z',
             'timestamp': 1495665551858},
 'is-referenced-by-count': 0,
 'issn-type': [{'type': 'electronic', 'value': '0102-311X'}],
 'issue': '11',
 'issued': {'date-parts': [[2016, 11]]},
 'member': '530',
 'original-title': [],
 'prefix': '10.1590',
 'published-print': {'date-parts': [[2016, 11]]},
 'publisher': 'FapUNIFESP (SciELO)',
 'reference-count': 3,
 'references-count': 3,
 'relation': {},
 'score': 1.0,
 'short-container-title': ['Cad. Saúde Pública'],
 'short-title': [],
 'source': 'Crossref',
 'subject': ['Medicine(all)'],
 'subtitle': [],
 'title': ['Congenital Zika virus syndrome'],
 'type': 'journal-article',
 'volume': '32'}
'''

# Select


for i in works.filter(has_funder='true', has_license='true').sample(5).select('DOI, prefix'):
    print(i)
'''
{'DOI': '10.1111/str.12144', 'member': 'http://id.crossref.org/member/311', 'prefix': '10.1111'}
{'DOI': '10.1002/admi.201400154', 'member': 'http://id.crossref.org/member/311', 'prefix': '10.1002'}
{'DOI': '10.1016/j.surfcoat.2010.10.057', 'member': 'http://id.crossref.org/member/78', 'prefix': '10.1016'}
{'DOI': '10.1007/s10528-015-9707-8', 'member': 'http://id.crossref.org/member/297', 'prefix': '10.1007'}
{'DOI': '10.1016/j.powtec.2016.04.009', 'member': 'http://id.crossref.org/member/78', 'prefix': '10.1016'}
'''

# Facet

works.facet('issn', 10)
'''
{'issn': {'value-count': 10,
          'values': {'http://id.crossref.org/issn/0009-2975': 306546,
                     'http://id.crossref.org/issn/0028-0836': 395353,
                     'http://id.crossref.org/issn/0140-6736': 458909,
                     'http://id.crossref.org/issn/0302-9743': 369955,
                     'http://id.crossref.org/issn/0931-7597': 487523,
                     'http://id.crossref.org/issn/0959-8138': 392754,
                     'http://id.crossref.org/issn/1095-9203': 253978,
                     'http://id.crossref.org/issn/1468-5833': 388355,
                     'http://id.crossref.org/issn/1556-5068': 273653,
                     'http://id.crossref.org/issn/1611-3349': 329573}}}

prefixes = Prefixes()

prefixes.works('10.1590').facet('issn', 10)

{'issn': {'value-count': 10,
          'values': {'http://id.crossref.org/issn/0004-282X': 7712,
                     'http://id.crossref.org/issn/0034-8910': 4752,
                     'http://id.crossref.org/issn/0037-8682': 4179,
                     'http://id.crossref.org/issn/0074-0276': 7941,
                     'http://id.crossref.org/issn/0100-204X': 3946,
                     'http://id.crossref.org/issn/0100-4042': 4198,
                     'http://id.crossref.org/issn/0102-311X': 6548,
                     'http://id.crossref.org/issn/0103-8478': 6607,
                     'http://id.crossref.org/issn/1413-8123': 4658,
                     'http://id.crossref.org/issn/1516-3598': 4678}}}

prefixes.works('10.1590').query('zika').facet('issn', 10)

{'issn': {'value-count': 10,
          'values': {'http://id.crossref.org/issn/0004-282X': 4,
                     'http://id.crossref.org/issn/0036-4665': 4,
                     'http://id.crossref.org/issn/0037-8682': 7,
                     'http://id.crossref.org/issn/0074-0276': 7,
                     'http://id.crossref.org/issn/0102-311X': 12,
                     'http://id.crossref.org/issn/0103-7331': 2,
                     'http://id.crossref.org/issn/0104-4230': 3,
                     'http://id.crossref.org/issn/1519-3829': 7,
                     'http://id.crossref.org/issn/1679-4508': 2,
                     'http://id.crossref.org/issn/1806-8324': 2}}}
'''
# Journals

# Exemplifying the use of API Library to retrieve data from Journals endpoint.

from crossref.restful import Journals

journals = Journals()

journals.journal('0102-311X')
'''
{'ISSN': ['0102-311X', '0102-311X'],
 'breakdowns': {'dois-by-issued-year': [[2013, 462],
                                        [2007, 433],
                                        [2008, 416],
                                        [2009, 347],
                                        [2006, 344],
                                        [2014, 292],
                                        [2004, 275],
                                        [2012, 273],
                                        [2011, 270],
                                        [2010, 270],
                                        [2005, 264],
                                        [2003, 257],
                                        [2001, 220],
                                        [2002, 219],
                                        [1998, 187],
                                        [2000, 169],
                                        [1997, 142],
                                        [1999, 136],
                                        [1994, 110],
                                        [1995, 104],
                                        [1996, 103],
                                        [1993, 99],
                                        [2015, 93],
                                        [1992, 65],
                                        [1986, 63],
                                        [1985, 53],
                                        [1990, 49],
                                        [1988, 49],
                                        [1991, 48],
                                        [1987, 46],
                                        [1989, 45]]},
 'counts': {'backfile-dois': 5565, 'current-dois': 335, 'total-dois': 5900},
 'coverage': {'award-numbers-backfile': 0.0,
              'award-numbers-current': 0.0,
              'funders-backfile': 0.0,
              'funders-current': 0.0,
              'licenses-backfile': 0.0,
              'licenses-current': 0.0,
              'orcids-backfile': 0.0,
              'orcids-current': 0.0,
              'references-backfile': 0.0,
              'references-current': 0.0,
              'resource-links-backfile': 0.0,
              'resource-links-current': 0.0,
              'update-policies-backfile': 0.0,
              'update-policies-current': 0.0},
 'flags': {'deposits': True,
           'deposits-articles': True,
           'deposits-award-numbers-backfile': False,
           'deposits-award-numbers-current': False,
           'deposits-funders-backfile': False,
           'deposits-funders-current': False,
           'deposits-licenses-backfile': False,
           'deposits-licenses-current': False,
           'deposits-orcids-backfile': False,
           'deposits-orcids-current': False,
           'deposits-references-backfile': False,
           'deposits-references-current': False,
           'deposits-resource-links-backfile': False,
           'deposits-resource-links-current': False,
           'deposits-update-policies-backfile': False,
           'deposits-update-policies-current': False},
 'last-status-check-time': 1459491023622,
 'publisher': 'SciELO',
 'title': 'Cadernos de Saúde Pública'}
'''
journals.journal_exists('0102-311X')

journals.query('Cadernos').url

journals.query('Cadernos').count()

journals.works('0102-311X').query('zika').url

journals.works('0102-311X').query('zika').count()

journals.works('0102-311X').query('zika').query(author='Diniz').url

journals.works('0102-311X').query('zika').query(author='Diniz').count()

journals = Journals()

# Count

# This method returns the total of itens a query result should retrive. 
# This method will not iterate and retrieve through the API documents. 
# This method will fetch 0 documents and retrieve the value of total-result attribute.

works.query('zika').count()

works.query('zika').filter(from_online_pub_date='2017').count()

# Url

# This method returns the url that will be used to query the Crossref API.

# works.query('zika').url
# 'https://api.crossref.org/works?query=zika'

works.query('zika').filter(from_online_pub_date='2017').url
# 'https://api.crossref.org/works?query=zika&filter=from-online-pub-date%3A2017'

works.query('zika').filter(from_online_pub_date='2017').query(author='Mari').url
# 'https://api.crossref.org/works?query.author=Mari&filter=from-online-pub-date%3A2017&query=zika'

works.query('zika').filter(from_online_pub_date='2017').query(author='Mari').sort('published').url
# 'https://api.crossref.org/works?query.author=Mari&query=zika&filter=from-online-pub-date%3A2017&sort=published'

works.query('zika').filter(from_online_pub_date='2017').query(author='Mari').sort('published').order('asc').url
# 'https://api.crossref.org/works?filter=from-online-pub-date%3A2017&query.author=Mari&order=asc&query=zika&sort=published'

prefixes = Prefixes()

prefixes.works('10.1590').query('zike').url
# 'https://api.crossref.org/prefixes/10.1590/works?query=zike'

journals.url
# 'https://api.crossref.org/journals'

journals.works('0102-311X').url
# 'https://api.crossref.org/journals/0102-311X/works'

journals.works('0102-311X').query('zika').url
# 'https://api.crossref.org/journals/0102-311X/works?query=zika'

journals.works('0102-311X').query('zika').count()
# 12

# All

# This method returns all items of an endpoint.
# It will use the limit offset parameters to iterate through the endpoints Journals, Types, Members and Prefixes.

# For the works endpoint, the library will make use of the cursor to paginate through API until it is totally consumed.

for item in journals.all():
    print(item['title'])

# Support for Polite Requests (Etiquette)

# Respecting the Crossref API polices for polite requests.
# This library allows users to setup an Etiquette object to be used in the http requests.

my_etiquette = Etiquette('My Project Name', 'My Project version', 'My Project URL', 'My contact email')

str(my_etiquette)
# 'My Project Name/My Project version (My Project URL; mailto:My contact email) BasedOn: CrossrefAPI/1.1.0'

my_etiquette = Etiquette('My Project Name', '0.2alpha', 'https://myalphaproject.com', 'anonymous@myalphaproject.com')

str(my_etiquette)
# 'My Project Name/0.2alpha (https://myalphaproject.com; mailto:anonymous@myalphaproject.com) BasedOn: CrossrefAPI/1.1.0'

works = Works(etiquette=my_etiquette)

for i in works.sample(5).select('DOI'):
    print(i)