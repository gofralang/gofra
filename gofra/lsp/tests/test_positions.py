"""Tests of the conversion between the compiler locations and the protocol positions."""

from pathlib import Path

from gofra.lsp.positions import (
    Position,
    location_to_position,
    location_to_range,
    position_to_index,
    utf16_length,
)
from libgofra.lexer.tokens import TokenLocation


def test_location_is_converted_to_a_zero_based_position() -> None:
    location = TokenLocation(
        filepath=Path("gofra.gof"),
        line_number=2,
        col_number=4,
    )

    position = location_to_position(location, ["first", "second", "third"])

    assert position.line == 2
    assert position.character == 4


def test_position_is_clamped_to_the_document() -> None:
    location = TokenLocation(
        filepath=Path("gofra.gof"),
        line_number=10,
        col_number=0,
    )

    position = location_to_position(location, ["first"])

    assert position.line == 10
    assert position.character == 0


def test_column_is_counted_in_utf16_code_units() -> None:
    location = TokenLocation(
        filepath=Path("gofra.gof"),
        line_number=0,
        col_number=3,
    )

    position = location_to_position(location, ["a🐍b"])

    assert position.character == 4


def test_utf16_length_counts_surrogate_pairs() -> None:
    assert utf16_length("abc") == 3
    assert utf16_length("🐍") == 2
    assert utf16_length("a🐍b") == 4


def test_range_covers_the_given_length() -> None:
    location = TokenLocation(
        filepath=Path("gofra.gof"),
        line_number=0,
        col_number=2,
    )

    location_range = location_to_range(location, ["abc"], length=3)

    assert location_range.start == Position(line=0, character=2)
    assert location_range.end == Position(line=0, character=5)


def test_position_is_converted_to_an_index() -> None:
    lines = ["first", "second"]

    assert position_to_index(Position(line=0, character=2), lines) == 2
    assert position_to_index(Position(line=1, character=0), lines) == 0
    assert position_to_index(Position(line=5, character=0), lines) == 0
