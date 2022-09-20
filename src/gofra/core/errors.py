"""
    'Gofra' errors module.
    Contains all stuff releated to the errors reporting part.
"""

from sys import stderr
from .danger import *


def message(level: str, text: str, force_exit: bool = False):
    """
    Show error to the console.
    :param level: String with message level.
    :param text: Text to display,
    :param force_exit: If true, will force exiting application.
    """

    print(f"[{level}] {text}", file=stderr)

    if force_exit:
        exit(1)


def message_verbosed(
    stage: Stage, location: LOCATION, level: str, text: str, force_exit: bool = False
):
    """
    Show verbosed error to the console.
    :param stage: TODO.
    :param location: TODO.
    :param level: String with message level.
    :param text: str,
    :param force_exit: If true, will force exiting application.
    """

    print(
        f"[{level} at `{stage}` stage] "  # STAGE_TYPES_TO_NAME[
        f"({location[0]}) on {location[1]}:{location[2]} - {text}",
        file=stderr,
    )

    if force_exit:
        exit(1)
