import urllib.parse

GOBCAN_BASE_URL = 'https://www.gobiernodecanarias.org'
EDU_APPOINTMENTS_BASE_URL = urllib.parse.urljoin(
    GOBCAN_BASE_URL,
    '/educacion/web/personal/docente/oferta/interinos-sustitutos/oferta_extraordinaria/',
)
