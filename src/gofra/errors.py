"""
    'Gofra' errors module.
    Contains all stuff releated to the errors reporting part.
"""

from sys import stderr


def message(level: str, text: str, force_exit: bool = False):
    """
    Show error to the console.
    :param: level String with message level.
    :param: text str,
    :param: force_exit If true, will force exiting application.
    """

    print(f"[{level}] {text}", file=stderr)

    if force_exit:
        exit(1)
