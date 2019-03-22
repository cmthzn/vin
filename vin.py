import requests
import datetime
import urllib3
from bs4 import BeautifulSoup
from libvin.decoding import Vin

urllib3.disable_warnings() # jakby mi nie pierdolily sie certyfikaty to bym nie dawal 
proxy   = ""  # wpisz se jak chcesz przez proxy jakies, np. https://109.108.90.87:8080

num_vin = input('Podaj VIN: ')
num_reg = input('Podaj nr rejestracyjny: ')
year = input('Podaj rok pierwszej rejestracji w Polsce: ')
num_reg = num_reg.replace(' ', '')

print("Proszę czekać...")

dt = datetime.datetime(int(year), 1, 1)
end = datetime.datetime(int(year), 12, 31)
step = datetime.timedelta(days=1)

result = []

while dt < end:
    result.append(dt.strftime('%d.%m.%Y'))
    dt += step

s = requests.Session()
req = s.get("https://historiapojazdu.gov.pl/", verify=False, proxies={"http": proxy, "https": proxy})
soup = BeautifulSoup(req.text, "lxml")
url = soup.find('form', {'id': '_historiapojazduportlet_WAR_historiapojazduportlet_:formularz'})['action']

for date in result:
    data = {
        "_historiapojazduportlet_WAR_historiapojazduportlet_:rej": num_reg, 
        "_historiapojazduportlet_WAR_historiapojazduportlet_:vin": num_vin, 
        "_historiapojazduportlet_WAR_historiapojazduportlet_:data": date,
        "_historiapojazduportlet_WAR_historiapojazduportlet_:formularz": "_historiapojazduportlet_WAR_historiapojazduportlet_:formularz",
        "_historiapojazduportlet_WAR_historiapojazduportlet_:btnSprawdz": "Sprawdź+pojazd+»",
        "javax.faces.ViewState": soup.find('input', {'name':'javax.faces.ViewState'})['value'],
        "javax.faces.encodedURL": soup.find('input', {'name':'javax.faces.encodedURL'})['value']
        }
    r = s.post(url, data=data, verify=False, proxies={"http": proxy, "https": proxy})
    if "RAPORT O POJEŹDZIE" not in r.text:
        #print('%s - nie znaleziono' % date)
        continue
    else:
        #print('> %s < - ZNALEZIONO !!!' % date)
        break

# gównokod alert
soup = BeautifulSoup(r.content, "lxml")
typ = soup.find('span', {'id': '_historiapojazduportlet_WAR_historiapojazduportlet_:j_idt7:typ'}).text
model = soup.find('span', {'id': '_historiapojazduportlet_WAR_historiapojazduportlet_:j_idt7:model'}).text
status = soup.find('p', {'class': 'status'}).text
docs = soup.findAll('div', {'class': 'group-text'})[6].text.split("    ")
docs = '\n'.join(docs).replace('   ', ' ').lstrip()
owners = soup.findAll('div', {'class': 'group-box'})[0].text.split("  ")
owners = '\n'.join(owners).replace('Podsumowanie zdarzeń:', '').replace('\n\n','\n').lstrip()
atm = soup.findAll('div', {'class': 'group-box'})[1].text.split("  ")
atm = '\n'.join(atm).replace('Stan aktualny:', '').replace('\n\n','\n').lstrip()

vin = Vin(num_vin)
info = '''
Marka: {}
Model: {} {}
Rok produkcji: {}
Producent: {}

VIN: {}
Numer rejestracyjny: {}
Data pierwszej rejestracji: {}

{}
{}{}{}Informacje techniczne: https://pl.vindecoder.eu/check-vin/VF30UAHRMFS276388'''.format(vin.make, typ, model, str(vin.year), vin.manufacturer, num_vin, num_reg, date, status, docs, owners, atm)

with open(num_vin+".txt", "w", encoding='utf-8') as f:   
    f.write(info)
    f.close()
    print(info)
