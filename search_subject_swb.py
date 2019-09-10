import urllib.parse
import urllib.request
from bs4 import BeautifulSoup


def search_subject(year, search_subject_title, search_subject_person, title, recent_record):
    url = "http://swb.bsz-bw.de/sru/DB=2.1/username=/password=/?query=pica.ejh+%3D+%22" + year + "%22+and+pica.tit+%3D+" + search_subject_title + "+and+pica.pne+%3D+%22" + search_subject_person + "%22&version=1.1&operation=searchRetrieve&stylesheet=http%3A%2F%2Fswb.bsz-bw.de%2Fsru%2FDB%3D2.362%2F%3Fxsl%3DsearchRetrieveResponse&recordSchema=marc21&maximumRecords=10&startRecord=1&recordPacking=xml&sortKeys=none&x-info-5-mg-requestGroupings=none"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        subject_page = response.read()
    subject_page = subject_page.decode('utf-8')
    subject_soup = BeautifulSoup(subject_page, 'html.parser')
    if len(subject_soup.find_all('datafield', tag="245")) == 0:
        search_subject_title = search_subject_title.split(".")[0].split("%2C%20")[0].split("%28")[0]
        url = "http://swb.bsz-bw.de/sru/DB=2.1/username=/password=/?query=pica.ejh+%3D+%22" + year + "%22+and+pica.tit+%3D+" + search_subject_title + "+and+pica.pne+%3D+%22" + search_subject_person + "%22&version=1.1&operation=searchRetrieve&stylesheet=http%3A%2F%2Fswb.bsz-bw.de%2Fsru%2FDB%3D2.362%2F%3Fxsl%3DsearchRetrieveResponse&recordSchema=marc21&maximumRecords=10&startRecord=1&recordPacking=xml&sortKeys=none&x-info-5-mg-requestGroupings=none"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            subject_page = response.read()
        subject_page = subject_page.decode('utf-8')
        subject_soup = BeautifulSoup(subject_page, 'html.parser')
    if subject_soup.find_all('datafield', tag="689") != None:
        if len(subject_soup.find_all('datafield', tag="689")) != 0:
            row = [title]
            for subject in subject_soup.find_all('datafield', tag="689"):
                if subject.find('subfield', code="D") != None:
                    indicator = subject.find('subfield', code="D").text
                    subject_name = subject.find('subfield', code="a").text
                    if subject_name not in row:
                        row.append(indicator)
                        row.append(subject_name)