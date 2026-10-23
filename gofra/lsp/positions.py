"""Conversion between compiler source locations and LSP positions.

The compiler reports locations as 0-based line numbers with 0-based column
numbers counted in unicode code points, while the protocol expects 0-based
lines and 0-based characters counted in UTF-16 code units.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Sequence

    from libgofra.lexer.tokens import TokenLocation

#: Number of code units that a single astral plane character takes in UTF-16.
UTF16_SURROGATE_WIDTH: Final = 2


@dataclass(frozen=True, slots=True)
class Position:
    """Zero based position inside a document."""

    line: int
    character: int

    def to_lsp(self) -> dict[str, int]:
        """Convert the position into the protocol representation."""
        return {"line": self.line, "character": self.character}


@dataclass(frozen=True, slots=True)
class Range:
    """Range inside a document."""

    start: Position
    end: Position

    def to_lsp(self) -> dict[str, dict[str, int]]:
        """Convert the range into the protocol representation."""
        return {"start": self.start.to_lsp(), "end": self.end.to_lsp()}


def utf16_length(text: str) -> int:
    """Get the length of the given text in UTF-16 code units."""
    return len(text) + sum(1 for char in text if ord(char) > 0xFFFF)


def utf16_offset_to_index(text: str, utf16_offset: int) -> int:
    """Convert an UTF-16 code unit offset into an index in the given text."""
    if utf16_offset <= 0:
        return 0

    units = 0
    for index, char in enumerate(text):
        if units >= utf16_offset:
            return index
        units += UTF16_SURROGATE_WIDTH if ord(char) > 0xFFFF else 1

    return len(text)


def location_to_position(
    location: TokenLocation,
    lines: Sequence[str],
) -> Position:
    """Convert a compiler source location into a protocol position."""
    line_index = max(location.line_number, 0)

    if line_index >= len(lines):
        return Position(line=line_index, character=0)

    prefix = lines[line_index][: max(location.col_number, 0)]
    return Position(line=line_index, character=utf16_length(prefix))


def location_to_range(
    location: TokenLocation,
    lines: Sequence[str],
    *,
    length: int = 1,
) -> Range:
    """Convert a compiler source location into a protocol range."""
    start = location_to_position(location, lines)
    end = Position(line=start.line, character=start.character + length)
    return Range(start=start, end=end)


def position_to_index(position: Position, lines: Sequence[str]) -> int:
    """Convert a protocol position into an index inside the given lines."""
    if position.line < 0 or position.line >= len(lines):
        return 0

    line = lines[position.line]
    return utf16_offset_to_index(line, position.character)
