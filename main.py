import requests
from bs4 import BeautifulSoup

import config
import utils

response = requests.get(config.EDU_APPOINTMENTS_BASE_URL)
soup = BeautifulSoup(response.content, 'html.parser')

for group in soup.find_all('h4'):
    print(group.text.strip())
    group_url = utils.build_absolute_url(group.a['href'])
    print(group_url)

    response = requests.get(group_url)
    gsoup = BeautifulSoup(response.content, 'html.parser')
    for offer in gsoup.find_all('li', class_='enlace-con-icono documento'):
        offer_link = offer.h4.a
        print(offer_link.text.strip())
        offer_url = utils.build_absolute_url(offer_link['href'])
        print(offer_url)
