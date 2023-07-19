import requests
from bs4 import BeautifulSoup

import settings
from lib import utils


class Offer:
    def __init__(self, url: str, name: str):
        self.url = url
        self.name = name

    def __str__(self):
        return self.name


class EduGroup:
    def __init__(self, url: str):
        self.url = url
        response = requests.get(self.url)
        self.soup = BeautifulSoup(response.content, 'html.parser')
        self.name = self.soup.find('h2', class_='titulo-modernizacion').text.strip()
        self.offers = self.get_offers()

    def get_offers(self):
        for offer in self.soup.find_all('li', class_='enlace-con-icono documento'):
            offer_link = offer.h4.a
            offer_url = utils.build_absolute_url(offer_link['href'])
            offer_name = offer_link.text.strip()
            offer = Offer(offer_url, offer_name)
            yield offer

    def __str__(self):
        return self.name

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.offers)


class Manager:
    def __init__(self, url: str = settings.EDU_APPOINTMENTS_BASE_URL):
        self.url = url
        response = requests.get(self.url)
        self.soup = BeautifulSoup(response.content, 'html.parser')

        for group in self.soup.find_all('h4'):
            group_url = utils.build_absolute_url(group.a['href'])
            edugroup = EduGroup(group_url)
            print("====================================")
            print(edugroup)
            print("====================================")
            for offer in edugroup:
                print(offer)
