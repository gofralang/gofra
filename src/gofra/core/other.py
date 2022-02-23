"""
    'Gofra' other module.
    Contains all stuff releated to the utils/other.
"""

from typing import Tuple, Optional, IO

from src.gofra.core import errors


def try_open_file(path: str, mode: str, force_exit: bool = False, **kwargs) -> Tuple[Optional[IO], bool]:
    """
    Tries to open file.
    :param path: File path.
    :param mode: File open mode.
    :param force_exit: If true, will raise exit on error.
    :returns: Tuple with (IO, status) where first element is the file, and second - status.
    """
    try:
        file = open(path, mode, **kwargs)
        return file, True
    except FileNotFoundError:
        errors.message("Error", f"File \"{path}\" failed to open because it was not founded!", force_exit)
    except (OSError, IOError, PermissionError) as error:
        errors.message("Error", f"File \"{path}\" failed to open because unexpected error: {error}", force_exit)
    return None, False