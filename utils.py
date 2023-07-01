import urllib.parse

import config


def build_absolute_url(url_path: str, base_url: str = config.GOBCAN_BASE_URL):
    return urllib.parse.urljoin(base_url, url_path)
