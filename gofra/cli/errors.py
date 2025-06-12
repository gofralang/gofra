from collections.abc import Generator
from contextlib import contextmanager

from gofra.exceptions import GofraError

from .output import cli_message


@contextmanager
def cli_gofra_error_handler() -> Generator[None]:
    """Wrap function to properly emit Gofra internal errors."""
    try:
        yield
    except GofraError as ge:
        cli_message("ERROR", repr(ge))
