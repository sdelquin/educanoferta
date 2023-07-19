import re
import shelve
import tempfile

import bs4
import PyPDF2
import requests
from bs4 import BeautifulSoup
from logzero import logger

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
    archive = shelve.open(settings.ARCHIVE_DB_PATH)

    def __init__(self, node: bs4.element.Tag):
        logger.info('🧱 Building appointment offer')
        offer_link = node.h4.a
        self.url = utils.build_absolute_url(offer_link['href'])
        self.name = offer_link.text.strip()
        logger.debug(f'🏄‍♂️ {self.url}')
        logger.debug(f'Name: {self.name}')
        self.download_offer()
        self.specialities = self.extract_specialities()

    def download_offer(self):
        logger.debug('🚀 Downloading appointment offer file')
        response = requests.get(self.url)
        self.filepath = tempfile.NamedTemporaryFile().name
        with open(self.filepath, 'wb') as f:
            f.write(response.content)

    def extract_specialities(self) -> list[Speciality]:
        logger.debug('🍿 Extracting specialities')
        speciality_codes = set()
        pdf = PyPDF2.PdfReader(self.filepath)
        for page in pdf.pages:
            contents = page.extract_text()
            for speciality_code in re.findall(r'\D([2-9]\d{1,2})\s*\.?[\-–]', contents):
                speciality_codes.add(int(speciality_code))
            for speciality_code in re.findall(r'\((\d{2})\)', contents):
                speciality_codes.add(int(speciality_code))

        logger.debug('Filtering valid specialities')
        valid_specialities = []
        for speciality_code in speciality_codes:
            try:
                speciality = Speciality(speciality_code)
            except KeyError:
                logger.error(f'💩 Speciality code {speciality_code} not found in DB')
            else:
                logger.debug(f'✨ Adding speciality "{speciality}"')
                valid_specialities.append(speciality)
        return sorted(valid_specialities)

    @property
    def already_notified(self) -> bool:
        return self.archive.get(self.id) is not None

    @property
    def id(self) -> str:
        return self.url

    def save(self):
        logger.debug('💾 Saving appointment offer')
        self.archive[self.id] = True

    def __str__(self):
        return self.name


class EduGroup:
    def __init__(self, url: str):
        logger.info(f'🧑‍🏫 Building EduGroup from {url}')
        self.url = url

        logger.debug('Making http request')
        response = requests.get(self.url)
        logger.debug('Creating the beautiful soup')
        self.soup = BeautifulSoup(response.content, 'html.parser')
        self.name = self.soup.find('h2', class_='titulo-modernizacion').text.strip()
        logger.debug(f'📋 Group name: {self.name}')

        self.offers = self.get_offers()

    def get_offers(self):
        logger.info('Getting appointment offers')
        for offer_node in self.soup.find_all('li', class_='enlace-con-icono documento'):
            yield Offer(offer_node)

    def __str__(self):
        return self.name

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.offers)


class Manager:
    def __init__(self, url: str = settings.EDU_APPOINTMENTS_BASE_URL):
        logger.info(f'Building Manager from {url}')
        self.url = url
        logger.debug('Making http request')
        response = requests.get(self.url)
        logger.debug('Creating the beautiful soup')
        self.soup = BeautifulSoup(response.content, 'html.parser')

    def dispatch(self):
        logger.debug('Dispatching educational teacher groups')
        for group in self.soup.find_all('h4'):
            group_url = utils.build_absolute_url(group.a['href'])
            edugroup = EduGroup(group_url)
            for offer in edugroup:
                if offer.already_notified:
                    logger.warning('🚫 Offer already notified. Discarding!')
                else:
                    offer.save()
