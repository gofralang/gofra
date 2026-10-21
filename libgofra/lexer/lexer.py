"""Character-driven lexer that splits Gofra source code into tokens.

Token boundaries are determined by the character class (and not by whitespace), so
`a+b` is three tokens (`a`, `+`, `b`) exactly like `a + b` is.

Whitespace still matters in a few places and is tracked explicitly on each token
(`has_leading_whitespace` / `has_trailing_whitespace`):

- `&x` (glued) is an address-of, while `& x` (separated) is a bitwise-and operator;
- `a.b` (glued) is a field accessor, while `a . b` (separated) is not.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Literal

from libgofra.lexer._state import LexerState
from libgofra.lexer.errors.unknown_preprocessor_directive import (
    UnknownPreprocessorDirectiveError,
)
from libgofra.lexer.errors.unknown_symbol import UnknownSymbolError
from libgofra.lexer.keywords import WORD_TO_KEYWORD, WORD_TO_PREPROCESSOR_KEYWORD
from libgofra.lexer.literals.character import tokenize_character_literal
from libgofra.lexer.literals.numeric import DECIMAL_DIGITS, scan_number
from libgofra.lexer.literals.string import tokenize_string_literal
from libgofra.lexer.symbols import (
    STRUCTURAL_SYMBOL_TO_TOKEN_TYPE,
    match_symbol_at,
)
from libgofra.lexer.tokens import Token, TokenType

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable
    from pathlib import Path


SINGLE_LINE_COMMENT = "//"


def tokenize_from_raw(
    source: Path | Literal["cli", "toolchain"],
    lines: Iterable[str],
) -> Generator[Token]:
    """Stream lexical tokens via generator (perform lexical analysis).

    :returns tokenizer: Generator of tokens, in order from top to bottom of an file (default order)
    """
    state = LexerState(source=source)

    for row, line in enumerate(lines, start=0):
        state.set_line(row, line)

        yield from _tokenize_line(state)

        yield Token(
            type=TokenType.EOL,
            text="\n",
            value=0,
            location=state.current_location(),
        )

    yield Token(
        type=TokenType.EOF,
        text="",
        value=0,
        location=state.current_location(),
    )


def _tokenize_line(state: LexerState) -> Generator[Token]:
    """Tokenize a single line of source code."""
    line = state.line
    length = len(line)

    # There is always a line break between a previous token and the first token of a line
    has_leading_whitespace = True

    while state.col < length:
        current = line[state.col]

        if current.isspace():
            state.col += 1
            has_leading_whitespace = True
            continue

        if line.startswith(SINGLE_LINE_COMMENT, state.col):
            # Line comment - skip the rest of the line
            state.col = length
            break

        token = _tokenize_next_token(state)
        yield _with_adjacency(
            token,
            state,
            has_leading_whitespace=has_leading_whitespace,
        )
        has_leading_whitespace = False


def _tokenize_next_token(state: LexerState) -> Token:  # noqa: PLR0911
    """Tokenize a single token at the current cursor position."""
    line = state.line
    col = state.col
    current = line[col]

    if current == '"':
        return tokenize_string_literal(state)
    if current == "'":
        return tokenize_character_literal(state)
    if current == "#":
        return _tokenize_preprocessor_directive(state)
    if current in DECIMAL_DIGITS:
        return scan_number(state)
    if current in "+-" and _is_digit_at(line, col + 1):
        # A sign that is directly followed by a digit is a part of the number literal
        return scan_number(state)
    if _is_identifier_start(current):
        return _tokenize_identifier(state)

    symbol = match_symbol_at(line, col)
    if symbol is None:
        raise UnknownSymbolError(at=state.current_location(), symbol=current)

    return _tokenize_symbol(state, symbol)


def _tokenize_identifier(state: LexerState) -> Token:
    """Tokenize an identifier (or a keyword) at the current cursor position."""
    location = state.current_location()
    line = state.line
    start = state.col

    while state.col < len(line) and _is_identifier_part(line[state.col]):
        state.col += 1

    word = line[start:state.col]

    if keyword := WORD_TO_KEYWORD.get(word):
        return Token(
            type=TokenType.KEYWORD,
            text=word,
            location=location,
            value=keyword,
        )

    return Token(
        type=TokenType.IDENTIFIER,
        text=word,
        location=location,
        value=word,
    )


def _tokenize_symbol(state: LexerState, symbol: str) -> Token:
    """Tokenize a known symbol at the current cursor position.

    Symbols that have a dedicated token type are emitted as such, operator spellings
    are emitted as identifiers (and are resolved into operators by the parser).
    """
    location = state.current_location()
    state.col += len(symbol)

    if token_type := STRUCTURAL_SYMBOL_TO_TOKEN_TYPE.get(symbol):
        return Token(
            type=token_type,
            text=symbol,
            location=location,
            value=symbol,
        )

    return Token(
        type=TokenType.IDENTIFIER,
        text=symbol,
        location=location,
        value=symbol,
    )


def _tokenize_preprocessor_directive(state: LexerState) -> Token:
    """Tokenize a preprocessor directive (e.g `#define`) at the current cursor position."""
    location = state.current_location()
    line = state.line

    state.col += 1  # Skip the `#` symbol
    name_start = state.col
    while state.col < len(line) and _is_identifier_part(line[state.col]):
        state.col += 1

    name = line[name_start:state.col]
    directive = f"#{name}"

    if keyword := WORD_TO_PREPROCESSOR_KEYWORD.get(directive):
        return Token(
            type=TokenType.KEYWORD,
            text=directive,
            location=location,
            value=keyword,
        )

    raise UnknownPreprocessorDirectiveError(at=location, directive=directive)


def _with_adjacency(
    token: Token,
    state: LexerState,
    *,
    has_leading_whitespace: bool,
) -> Token:
    """Attach exact whitespace adjacency information to a token."""
    line = state.line
    has_trailing_whitespace = (
        state.col >= len(line)
        or line[state.col].isspace()
        or line.startswith(SINGLE_LINE_COMMENT, state.col)
    )

    return replace(
        token,
        has_leading_whitespace=has_leading_whitespace,
        has_trailing_whitespace=has_trailing_whitespace,
    )


def _is_identifier_start(char: str) -> bool:
    return char.isalpha() or char == "_"


def _is_identifier_part(char: str) -> bool:
    return char.isalnum() or char == "_"


def _is_digit_at(line: str, index: int) -> bool:
    return index < len(line) and line[index] in DECIMAL_DIGITS
