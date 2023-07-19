import re
import tempfile

import PyPDF2
import requests
from bs4 import BeautifulSoup

import settings
from lib import db, utils


class Speciality:
    def __init__(self, code: int):
        self.code = code
        self.name = db.get_specialities()[self.code]

    def __lt__(self, other):
        if isinstance(other, Speciality):
            return self.code < other.code
        return False

    def __repr__(self):
        return f'{self.code} {self.name}'


class Offer:
    def __init__(self, url: str, name: str):
        self.url = url
        self.name = name
        self.download_offer()
        self.specialities = self.extract_specialities()

    def download_offer(self):
        response = requests.get(self.url)
        self.filepath = tempfile.NamedTemporaryFile().name
        with open(self.filepath, 'wb') as f:
            f.write(response.content)

    def extract_specialities(self) -> list[Speciality]:
        speciality_codes = set()
        pdf = PyPDF2.PdfReader(self.filepath)
        for page in pdf.pages:
            contents = page.extract_text()
            for speciality_code in re.findall(r'\D([2-9]\d{1,2})\s*\.?[\-–]', contents):
                speciality_codes.add(int(speciality_code))
            for speciality_code in re.findall(r'\((\d{2})\)', contents):
                speciality_codes.add(int(speciality_code))

        valid_specialities = []
        for speciality_code in speciality_codes:
            try:
                speciality = Speciality(speciality_code)
            except KeyError:
                print(f'Speciality code {speciality_code} not found in DB')
            else:
                valid_specialities.append(speciality)
        return sorted(valid_specialities)

    def __str__(self):
        return self.name


class EduGroup:
    def __init__(self, url: str):
        self.url = url
        response = requests.get(self.url)
        self.soup = BeautifulSoup(response.content, 'html.parser')
        self.name = self.soup.find('h2', class_='titulo-modernizacion').text.strip()
        print("====================================")
        print(self.name)
        print("====================================")
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
            for offer in edugroup:
                pass
