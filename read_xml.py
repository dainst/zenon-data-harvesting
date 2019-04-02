record={}
import xml.etree.ElementTree as ET
tree = ET.parse('record_nr2.xml')
root = tree.getroot()
for child in root:
    print(child)
    if child.text==None:
        record[child.tag]={}
        for subchild in child.findall('{http://www.openarchives.org/OAI/2.0/oai_dc/}dc'):
            dc_dict={}
            #if subchild.text!=None:
                #record[child.tag][subchild.tag]=subchild.text
            for category in ['title','creator','subject','description','publisher','contributor','date','type','source','language',
                             'relation','coverage','rights','format','identifier']:
                dc_category=subchild.findall('{http://purl.org/dc/elements/1.1/}'+category)
                item_nr=0
                for item in dc_category:
                    if len(dc_category)==1:
                        dc_dict[str(item.tag)]=item.text
                    else:
                        dc_dict[str(item.tag)]=[]
                        for item in dc_category:
                            dc_dict[str(item.tag)].append(item.text)
            record[child.tag]=dc_dict
        print(record)