from contextlib import contextmanager
from typing import Generator

from gofra.exceptions import GofraError

from .output import cli_message


@contextmanager
def cli_user_error_handler() -> Generator[None]:
    try:
        yield
    except GofraError as ge:
        cli_message("ERROR", repr(ge))
