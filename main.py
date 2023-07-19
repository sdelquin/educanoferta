import logzero
import typer

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
    '''Nombrame: Notificación de nombramientos'''

    logger.setLevel(getattr(logzero, loglevel.upper()))
    manager = Manager()


if __name__ == "__main__":
    try:
        app()
    except Exception as err:
        logger.exception(err)
