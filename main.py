import glob
import os

import logzero
import typer

import settings
from lib.appointments import Manager
from lib.utils import init_logger

logger = init_logger()
app = typer.Typer(add_completion=False)


@app.command()
def run(
    loglevel: str = typer.Option(
        'DEBUG', '--loglevel', '-l', help='Log level (debug, info, error)'
    ),
):
    '''Notify educational appointment offers'''

    logger.setLevel(getattr(logzero, loglevel.upper()))
    manager = Manager()
    manager.dispatch()


@app.command()
def clear():
    '''Clear archive database.'''
    if typer.confirm('Are you sure to delete archive database?'):
        for file_path in glob.glob(str(settings.ARCHIVE_DB_PATH) + '*'):
            os.remove(file_path)


if __name__ == "__main__":
    try:
        app()
    except Exception as err:
        logger.exception(err)
