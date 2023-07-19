import csv
import functools
from pathlib import Path

import settings


@functools.cache
def get_specialities(db_path: str | Path = settings.SPECIALITIES_DB_PATH) -> dict[int, str]:
    with open(db_path) as f:
        reader = csv.reader(f, delimiter=settings.SPECIALITIES_DB_DELIMITER)
        return {int(code): title for code, title in reader}
