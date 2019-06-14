from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import time
driver = webdriver.Firefox()
driver.get("https://zenon.dainst.org/Search/Advanced")
assert "Advanced Search" in driver.title # stellt sicher, dass im Titel Python steht
elem = driver.find_element_by_id("search_lookfor0_0") #findet Element mit dem Attribut name="q" (Suchfeld)
elem.clear() #entfernt bereits gesetzte Angaben aus dem Suchfeld
elem.send_keys("\"Journal of late antiquity\"") #gibt den Text in das Suchfeld ein
category=Select(driver.find_element_by_id("search_type0_0"))
category.select_by_value("Title")
elem2 = driver.find_element_by_id("search_lookfor0_1") #findet Element mit dem Attribut name="q" (Suchfeld)
elem2.clear() #entfernt bereits gesetzte Angaben aus dem Suchfeld
elem2.send_keys("2008") #gibt den Text in das Suchfeld ein
category2=Select(driver.find_element_by_id("search_type0_1"))
category2.select_by_value("year")
elem2.send_keys(Keys.RETURN) #gibt Return in das Suchfeld ein
time.sleep(2)
titles_found=driver.find_elements_by_class_name("getFull")
if len(titles_found)==0:
    print("No such title found.")
if len(titles_found)==1:
    print("Der Titel ", titles_found[0].text, " ist in Zenon enthalten.")
    print("Der gesuchte Titel war: ", "split_title")
else:
    print("Es gibt mehrere Treffer zu Ihrer Suche. Diese lauten:")
    for title in titles_found:
        print(title.text)
driver.close()

