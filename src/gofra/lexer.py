"""
    Gofra Lexer module.

    Contains all stuff releated to lexer.
"""

from typing import Callable


def unescape(string: str) -> str:
    """
    Unescapes string.
    :param: string Value to unescape.
    :return: Unescaped string
    """
    return string.encode("UTF-8").decode("unicode_escape").encode("latin-1").decode("UTF-8")


def find_collumn(string: str, start: int, predicate: Callable[[str], bool]) -> int:
    """
    Finds column in the line from start that not triggers filter predicate.
    :param: strint Value to search inside.
    :param: start Index of the first character to start search from.
    :param: predicate Function that accepts charater and returns bool if it is end or not.
    :return: Index of the end.
    """
    end = len(string)
    while start < end and not predicate(string[start]):
        # While we don't reach end or not triggered predicate.
        start += 1
    return start
