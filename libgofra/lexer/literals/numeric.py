"""Lexer support for numeric literals."""

from __future__ import annotations

from typing import TYPE_CHECKING

from libgofra.lexer.errors.invalid_number_literal import InvalidNumberLiteralError
from libgofra.lexer.tokens import Token, TokenType

if TYPE_CHECKING:
    from libgofra.lexer._state import LexerState
    from libgofra.lexer.tokens import TokenLocation


DECIMAL_DIGITS = "0123456789"
HEXADECIMAL_DIGITS = "0123456789abcdefABCDEF"
BINARY_DIGITS = "01"
OCTAL_DIGITS = "01234567"

DIGIT_SEPARATOR = "_"


def scan_number(state: LexerState) -> Token:
    """Scan a numeric literal at the current cursor position.

    A sign (`+` or `-`) is a part of the literal when it is directly followed by a digit
    (e.g `-1` is a negative literal, while `1 - 1` is a subtraction).

    Supported literals: `123` `-123` `1_000` `0x1F` `0b1010` `0o777` `1.5` `1.5e10` `1.5e-10`.

    :raises InvalidNumberLiteralError: Number is malformed or is followed by a garbage.
    """
    location = state.current_location()
    start = state.col
    line = state.line

    sign = 1
    if line[state.col] in "+-":
        if line[state.col] == "-":
            sign = -1
        state.col += 1

    base, prefix_length, allowed_digits = _match_number_base(line, state.col)
    state.col += prefix_length

    int_digits = _scan_digits(state, allowed_digits)
    if not int_digits:
        raise InvalidNumberLiteralError(
            at=location,
            number_raw=line[start : state.col],
            reason="expected at least one digit in the number literal",
        )
    _ensure_valid_digit_separators(
        int_digits, location=location, number_raw=line[start : state.col],
    )

    fraction_digits = ""
    exponent_digits = ""
    exponent_sign = ""
    is_float = False

    if base == 10:
        if line[state.col : state.col + 1] == "." and _is_digit_at(state, 1):
            state.col += 1
            fraction_digits = _scan_digits(state, DECIMAL_DIGITS)
            _ensure_valid_digit_separators(
                fraction_digits,
                location=location,
                number_raw=line[start : state.col],
            )
            is_float = True

        if line[state.col : state.col + 1] in ("e", "E"):
            exponent_start = state.col
            state.col += 1
            if line[state.col : state.col + 1] in ("+", "-"):
                exponent_sign = line[state.col]
                state.col += 1
            exponent_digits = _scan_digits(state, DECIMAL_DIGITS)
            if not exponent_digits:
                # Not an exponent at all - rollback and let it be handled as a garbage
                state.col = exponent_start
            else:
                _ensure_valid_digit_separators(
                    exponent_digits,
                    location=location,
                    number_raw=line[start : state.col],
                )
                is_float = True

    number_raw = line[start : state.col]
    _ensure_number_ends(state, location=location, number_raw=number_raw)

    cleaned_int = int_digits.replace(DIGIT_SEPARATOR, "")
    if is_float:
        cleaned_fraction = fraction_digits.replace(DIGIT_SEPARATOR, "")
        cleaned_exponent = exponent_digits.replace(DIGIT_SEPARATOR, "")
        number_text = f"{cleaned_int}.{cleaned_fraction}"
        if cleaned_exponent:
            number_text += f"e{exponent_sign}{cleaned_exponent}"
        return Token(
            type=TokenType.FLOAT,
            text=number_raw,
            value=float(number_text) * sign,
            location=location,
        )

    return Token(
        type=TokenType.INTEGER,
        text=number_raw,
        value=int(cleaned_int, base) * sign,
        location=location,
    )


def _ensure_valid_digit_separators(
    digits: str,
    *,
    location: TokenLocation,
    number_raw: str,
) -> None:
    """Ensure that `_` digit separators are not placed at the edges or doubled."""
    if digits.startswith(DIGIT_SEPARATOR) or digits.endswith(DIGIT_SEPARATOR):
        raise InvalidNumberLiteralError(
            at=location,
            number_raw=number_raw,
            reason="digit separator cannot be placed at the start or at the end of a number",
        )
    if DIGIT_SEPARATOR * 2 in digits:
        raise InvalidNumberLiteralError(
            at=location,
            number_raw=number_raw,
            reason="digit separators cannot be doubled",
        )


def _match_number_base(
    line: str,
    col: int,
) -> tuple[int, int, str]:
    """Match a number base prefix (e.g `0x`) at given column.

    :returns: Tuple of (base, prefix length, allowed digits alphabet).
    """
    prefix = line[col : col + 2]
    if prefix in ("0x", "0X"):
        return 16, 2, HEXADECIMAL_DIGITS
    if prefix in ("0b", "0B"):
        return 2, 2, BINARY_DIGITS
    if prefix in ("0o", "0O"):
        return 8, 2, OCTAL_DIGITS
    return 10, 0, DECIMAL_DIGITS


def _scan_digits(state: LexerState, allowed_digits: str) -> str:
    """Consume digits (with optional `_` separators) at the cursor position."""
    start = state.col
    line = state.line
    while state.col < len(line):
        current = line[state.col]
        if current in allowed_digits:
            state.col += 1
            continue
        if current == DIGIT_SEPARATOR:
            state.col += 1
            continue
        break
    return line[start : state.col]


def _is_digit_at(state: LexerState, offset: int) -> bool:
    line = state.line
    index = state.col + offset
    return index < len(line) and line[index] in DECIMAL_DIGITS


def _ensure_number_ends(
    state: LexerState,
    *,
    location: TokenLocation,
    number_raw: str,
) -> None:
    """Ensure that a number literal is not directly followed by an identifier part."""
    line = state.line
    if state.col >= len(line):
        return

    current = line[state.col]
    if current.isalnum() or current == DIGIT_SEPARATOR:
        raise InvalidNumberLiteralError(
            at=location,
            number_raw=number_raw + current,
            reason="number literal is directly followed by an identifier part",
        )
