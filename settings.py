import urllib.parse

from prettyconf import config

GOBCAN_BASE_URL = config('GOBCAN_BASE_URL', default='https://www.gobiernodecanarias.org')
EDU_APPOINTMENTS_URL_PATH = config(
    'EDU_APPOINTMENTS_URL_PATH',
    default='/educacion/web/personal/docente/oferta/interinos-sustitutos/oferta_extraordinaria/',
)
EDU_APPOINTMENTS_BASE_URL = urllib.parse.urljoin(GOBCAN_BASE_URL, EDU_APPOINTMENTS_URL_PATH)
