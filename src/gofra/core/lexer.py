"""
    'Gofra' lexer module.
    Contains all stuff releated to the lexer part.
"""

from typing import Callable

# Constants.
__CHAR_ESCAPE = "\\"
__CHAR_STRING = '"'


def unescape(string: str) -> str:
    """
    Unescapes string.
    :param string: Value to unescape.
    :return: Unescaped string
    """
    return (
        string.encode("UTF-8")
        .decode("unicode_escape")
        .encode("latin-1")
        .decode("UTF-8")
    )


def find_collumn(string: str, start: int, predicate: Callable[[str], bool]) -> int:
    """
    Finds column in the line from start that not triggers filter predicate.
    :param string: Value to search inside.
    :param start: Index of the first character to start search from.
    :param predicate: Function that accepts charater and returns bool if it is end or not.
    :return: Index of the end.
    """
    end = len(string)
    while start < end and not predicate(string[start]):
        # While we don't reach end or not triggered predicate.
        start += 1
    return start


def find_string_end(string: str, start: int) -> int:
    """
    Search for end of string in the line
    :param string: String in which to search.
    :param start: Index of the start to search.
    """

    current_index = start
    character_previous = string[current_index]

    while current_index < len(string):
        # While we not reach end of the string.

        character_current = string[current_index]
        if character_current == __CHAR_STRING and character_previous != __CHAR_ESCAPE:
            break  # Reached unescaped string literal.

        character_previous = character_current
        current_index += 1

    return current_index
