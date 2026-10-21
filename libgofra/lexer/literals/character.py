"""Lexer support for character literals."""

from __future__ import annotations

from typing import TYPE_CHECKING

from libgofra.lexer.errors import (
    EmptyCharacterLiteralError,
    ExcessiveCharacterLengthError,
    UnclosedCharacterQuoteError,
)
from libgofra.lexer.helpers import (
    find_quoted_literal_end,
    unescape_text_literal,
)
from libgofra.lexer.tokens import Token, TokenType

if TYPE_CHECKING:
    from libgofra.lexer._state import LexerState


CHARACTER_QUOTE = "'"


def tokenize_character_literal(state: LexerState) -> Token:
    """Tokenize character quote at cursor into character literal token or raise error if invalid character."""
    assert state.line and state.line[state.col] == CHARACTER_QUOTE, (  # noqa: PT018
        f"{tokenize_character_literal.__name__} must be called when cursor is at open character quote"
    )

    location = state.current_location()
    start = state.col
    state.col += len(CHARACTER_QUOTE)

    ends_at = find_quoted_literal_end(state.line, state.col, quote=CHARACTER_QUOTE)
    if ends_at == -1:
        raise UnclosedCharacterQuoteError(open_quote_at=location)

    # Preserve literal as 'X' and unescaped version
    char_literal = state.line[start:ends_at]
    char = unescape_text_literal(char_literal[1:-1], at=location)

    if len(char) == 0:
        raise EmptyCharacterLiteralError(open_quote_at=location)
    if len(char) >= 2:
        raise ExcessiveCharacterLengthError(location, len(char))

    # Advance to next symbol
    state.col = ends_at
    return Token(
        type=TokenType.CHARACTER,
        text=char_literal,
        value=ord(char),  # Char-code
        location=location,
    )
