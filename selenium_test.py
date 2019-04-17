from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

driver = webdriver.Firefox()
driver.get("https://zenon.dainst.org/Search/Advanced")
assert "Advanced Search" in driver.title # stellt sicher, dass im Titel Python steht
elem = driver.find_element_by_name("search_lookfor0_0") #findet Element mit dem Attribut name="q" (Suchfeld)
elem.clear() #entfernt bereits gesetzte Angaben aus dem Suchfeld
elem.send_keys("Archäologie heute") #gibt den Text in das Suchfeld ein
category=Select(driver.find_element_by_id("search_type0_0"))
category.select_by_value("Title")
elem2 = driver.find_element_by_name("search_lookfor0_0") #findet Element mit dem Attribut name="q" (Suchfeld)
elem2.clear() #entfernt bereits gesetzte Angaben aus dem Suchfeld
elem2.send_keys("2008") #gibt den Text in das Suchfeld ein
category2=Select(driver.find_element_by_id("search_type0_0"))
category2.select_by_value("2008")
elem2.send_keys(Keys.RETURN) #gibt Return in das Suchfeld ein
assert "No results found." not in driver.page_source #stellt sicher, dass die Suche erfolgreich war

#driver.close()

