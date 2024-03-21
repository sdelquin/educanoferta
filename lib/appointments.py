from __future__ import annotations

import datetime
import re
import shelve
import tempfile

import bs4
import PyPDF2
import requests
from bs4 import BeautifulSoup
from logzero import logger
from slugify import slugify

import settings
from lib import db, utils
from lib.notification import TelegramBot


class Speciality:
    def __init__(self, code: int):
        self.code = code
        self.name = db.get_specialities()[self.code]

    def __lt__(self, other):
        if isinstance(other, Speciality):
            return slugify(self.name) < slugify(other.name)
        return False

    def __repr__(self):
        return f'({self.code}) {self.name}'


class Offer:
    archive = shelve.open(settings.ARCHIVE_DB_PATH)
    tgbot = TelegramBot()

    def __init__(self, node: bs4.element.Tag, edugroup: EduGroup):
        logger.info('🧱 Building appointment offer')

        self.edugroup = edugroup
        self.date, self.name = self._parse_title(node.text)
        self.url = utils.build_absolute_url(node['href'])
        logger.debug(f'🔵 {self.name}')
        logger.debug(f'{self.fdate}')
        logger.debug(f'{self.url}')

    def _parse_title(self, title: str) -> tuple[datetime.date, str]:
        if m := re.fullmatch(r'(?:\[(\d{2}/\d{2}/\d{4})\])?\s*(.*)', title.strip()):
            if offer_date := m[1]:
                date = datetime.datetime.strptime(offer_date, '%d/%m/%Y').date()
            else:
                raise ValueError(f'Unexpected title format: {title}')
            name = m[2]
            return date, name
        raise ValueError(f'Unexpected title format: {title}')

    @property
    def already_dispatched(self) -> bool:
        return self.archive.get(self.id) is not None

    @property
    def launched_today(self) -> bool:
        return self.date == datetime.date.today()

    @property
    def id(self) -> str:
        return self.url

    @property
    def as_markdown(self) -> str:
        return utils.render_message(
            settings.APPOINTMENT_TMPL_NAME, offer=self, hashtag=settings.NOTIFICATION_HASHTAG
        )

    @property
    def fdate(self) -> str:
        return self.date.strftime('%d/%m/%Y')

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
        """
        Estructura de una oferta para nombramiento:
        ul
         └─ li
             └─ h4
                 └─ a
        """

        def date_as_tuple(node: bs4.element.Tag) -> tuple[str, str, str]:
            try:
                title = node['title']
                if m := re.match(r'\[(?P<day>\d+)/(?P<month>\d+)/(?P<year>\d+)\]', title):
                    return m['year'], m['month'], m['day']
            except Exception as err:
                logger.exception(err)
            return '', '', ''

        OFFER_SELECTORS = [
            'ul.con-titulo>li.enlace-con-icono.documento>h4>a',
            'ul.con-titulo>li.titulo-subapartado>h4>a',
        ]

        logger.info('👀 Getting appointment offers')

        offer_nodes = []
        for offer_selector in OFFER_SELECTORS:
            offer_nodes.extend(self.soup.select(offer_selector))

        for offer_node in sorted(offer_nodes, key=date_as_tuple):
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
                elif not offer.launched_today:
                    logger.warning('🕒 Offer not launched today. Discarding!')
                else:
                    offer.download_offer()
                    offer.extract_specialities()
                    if notify:
                        offer.notify()
                    else:
                        logger.warning('🔕 Notification disabled by user')
                    offer.save()
