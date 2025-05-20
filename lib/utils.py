import functools
import urllib.parse
from pathlib import Path

import jinja2
import logzero
from telegramtk.utils import escape_markdown as em

import settings


def build_absolute_url(url_path: str, base_url: str = settings.GOBCAN_BASE_URL):
    return urllib.parse.urljoin(base_url, url_path)


def init_logger():
    logformat = (
        '%(asctime)s '
        '%(color)s'
        '[%(levelname)-8s] '
        '%(end_color)s '
        '%(message)s '
        '%(color)s'
        '(%(filename)s:%(lineno)d)'
        '%(end_color)s'
    )

    console_formatter = logzero.LogFormatter(fmt=logformat)
    file_formatter = logzero.LogFormatter(fmt=logformat, color=False)
    logzero.setup_default_logger(formatter=console_formatter)
    logzero.logfile(
        settings.LOGFILE,
        maxBytes=settings.LOGFILE_SIZE,
        backupCount=settings.LOGFILE_BACKUP_COUNT,
        formatter=file_formatter,
    )
    return logzero.logger


@functools.cache
def init_jinja():
    loader = jinja2.FileSystemLoader(settings.MSG_TEMPLATES_DIR)
    env = jinja2.Environment(loader=loader)
    env.filters['escape'] = lambda s: em(s) if isinstance(s, str) else em(str(s))
    return env


def render_message(template_name: Path, **args) -> str:
    jinja_env = init_jinja()
    template = jinja_env.get_template(template_name)
    return template.render(**args)
