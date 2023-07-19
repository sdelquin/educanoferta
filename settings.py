import urllib.parse
from pathlib import Path

from prettyconf import config

PROJECT_DIR = Path(__file__).parent
PROJECT_NAME = PROJECT_DIR.name
DATA_DIR = PROJECT_DIR / 'data'

GOBCAN_BASE_URL = config('GOBCAN_BASE_URL', default='https://www.gobiernodecanarias.org')
EDU_APPOINTMENTS_URL_PATH = config(
    'EDU_APPOINTMENTS_URL_PATH',
    default='/educacion/web/personal/docente/oferta/interinos-sustitutos/oferta_extraordinaria/',
)
EDU_APPOINTMENTS_BASE_URL = urllib.parse.urljoin(GOBCAN_BASE_URL, EDU_APPOINTMENTS_URL_PATH)
SPECIALITIES_DB_PATH = config(
    'SPECIALITIES_DB_PATH', default=DATA_DIR / 'specialities.csv', cast=Path
)
SPECIALITIES_DB_DELIMITER = config('SPECIALITIES_DB_DELIMITER', default=';')
UNKNOWN_SPECIALITY_NAME = config('UNKNOWN_SPECIALITY_NAME', default='DESCONOCIDO')

LOGFILE = config('LOGFILE', default=PROJECT_DIR / (PROJECT_NAME + '.log'), cast=Path)
LOGFILE_SIZE = config('LOGFILE_SIZE', cast=float, default=1e6)
LOGFILE_BACKUP_COUNT = config('LOGFILE_BACKUP_COUNT', cast=int, default=3)

ARCHIVE_DB_PATH = config('ARCHIVE_DB_PATH', default=DATA_DIR / 'archive.dbm', cast=Path)
