import urllib.parse

import settings


def build_absolute_url(url_path: str, base_url: str = settings.GOBCAN_BASE_URL):
    return urllib.parse.urljoin(base_url, url_path)
