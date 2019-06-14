import re
fields_776_w={}
with open('776.txt', 'r') as text:
    founds=0
    for line in text.readlines():
        found=re.findall(r'776..L\$\$.*?$',line)[0]
        only_776=re.findall(r'(776..L\$\$.*?)(?:\d{3}..L\$\$|$)',found)[0]
        if len(re.findall(r'\$\$w(.*?)(?:\d{3}..L\$\$|$)', only_776))>0:
            for item in re.findall(r'\$\$w(.*?)(?:\d{3}..L\$\$|$)', only_776)[0].split('OWN')[0].split('CAT')[0].split('LKR')[0][:-4].split('$$w'):
                fields_776_w[item]=re.findall(r' L(A*T*R*\d{9})\d{7} ', line)[0]
for item in sorted(fields_776_w.keys()):
    print("Systemnummer:", fields_776_w[item])
    print("$w:", item)

