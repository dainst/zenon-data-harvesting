from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import os

PDF_file = "test.pdf"
pages = convert_from_path(PDF_file, 500)
page_nr=0
for page in pages:
    page_nr+=1
    page.save('pages_jpg/test_'+str(page_nr)+'.jpg', 'JPEG')
txt=open('test.txt', mode='w+', encoding='utf-8')
for filename in os.listdir('pages_jpg'):
    text = str(((pytesseract.image_to_string(Image.open('pages_jpg/'+filename),lang="deu"))))
    txt.write(text)
txt.close()
#funktioniert halbwegs mit language-Kodierung