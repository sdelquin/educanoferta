from __future__ import annotations

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
from lib.notification import TelegramBot


class Speciality:
    def __init__(self, code: int):
        self.code = code
        self.name = db.get_specialities()[self.code]

    def __lt__(self, other):
        if isinstance(other, Speciality):
            return self.code < other.code
        return False

    def __repr__(self):
        return f'({self.code}) {self.name}'


class Offer:
    archive = shelve.open(settings.ARCHIVE_DB_PATH)
    tgbot = TelegramBot()

    def __init__(self, node: bs4.element.Tag, edugroup: EduGroup):
        logger.info('🧱 Building appointment offer')

        self.edugroup = edugroup
        offer_link = node.h4.a
        self.name = re.sub(r'\[\s*?([\d\/]+)\s*\]?', r'\1', offer_link.text.strip())
        self.url = utils.build_absolute_url(offer_link['href'])
        logger.debug(f'🔵 {self.name}')
        logger.debug(f'{self.url}')

    def download_offer(self) -> None:
        logger.debug('🚀 Downloading appointment offer file')
        response = requests.get(self.url)
        self.filepath = tempfile.NamedTemporaryFile().name
        with open(self.filepath, 'wb') as f:
            f.write(response.content)

    def extract_specialities(self) -> None:
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
        self.specialities = []
        for speciality_code in speciality_codes:
            try:
                speciality = Speciality(speciality_code)
            except KeyError:
                logger.error(f'💩 Speciality code {speciality_code} not found in DB')
            else:
                logger.debug(f'✨ Adding speciality "{speciality}"')
                self.specialities.append(speciality)
        self.specialities.sort()

    @property
    def already_dispatched(self) -> bool:
        return self.archive.get(self.id) is not None

    @property
    def id(self) -> str:
        return self.url

    @property
    def as_markdown(self) -> str:
        return utils.render_message(
            settings.APPOINTMENT_TMPL_NAME, offer=self, hashtag=settings.NOTIFICATION_HASHTAG
        )

    def save(self) -> None:
        logger.debug('💾 Saving appointment offer')
        self.archive[self.id] = True

    def notify(self, telegram_chat_id: str = settings.TELEGRAM_CHAT_ID) -> None:
        self.tgbot.send(telegram_chat_id, self.as_markdown)

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
        for offer_node in reversed(self.soup.find_all('li', class_='enlace-con-icono documento')):
            try:
                yield Offer(offer_node, self)
            except Exception as err:
                logger.exception(err)

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

    def dispatch(self, notify: bool = True):
        logger.debug('Dispatching educational teacher groups')
        for group in self.soup.find_all('h4'):
            group_url = utils.build_absolute_url(group.a['href'])
            edugroup = EduGroup(group_url)
            for offer in edugroup:
                if offer.already_dispatched:
                    logger.warning('🚫 Offer already dispatched. Discarding!')
                else:
                    offer.download_offer()
                    offer.extract_specialities()
                    if notify:
                        offer.notify()
                    else:
                        logger.warning('🔕 Notification disabled by user')
                    offer.save()
