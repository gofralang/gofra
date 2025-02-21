from __future__ import annotations

from collections.abc import Generator, Sequence
from typing import TYPE_CHECKING

from gofra.lexer.keywords import WORD_TO_KEYWORD

from ._context import LexerContext
from .exceptions import (
    LexerEmptyCharacterError,
    LexerExcessiveCharacterLengthError,
    LexerUnclosedCharacterQuoteError,
    LexerUnclosedStringQuoteError,
)
from .helpers import (
    find_string_end,
    find_word_end,
    find_word_start,
    unescape_string,
)
from .tokens import Token, TokenLocation, TokenType

if TYPE_CHECKING:
    from pathlib import Path

type TokenGenerator = Generator[Token, None, LexerContext]


def load_file_for_lexical_analysis(
    source_filepath: Path,
) -> TokenGenerator:
    """Load file to read and stream resulting lexical tokens.

    Propagates source file path so can be used for module file resolution

    Returns tokens in default order (ordered)
    """
    with source_filepath.open(
        errors="strict",
        buffering=1,
        newline="",
        encoding="UTF-8",
    ) as fd:
        source_file_lines = fd.readlines(-1)

    context = yield from _perform_lexical_analysis(
        lines=source_file_lines,
        source_filepath=source_filepath,
    )
    return context


def _perform_lexical_analysis(
    lines: Sequence[str],
    source_filepath: Path,
) -> TokenGenerator:
    """Convert source lines of text into stream of tokens.

    TODO(@kirillzhosul): Input is not an stream, we may introduce generator sending with lines
    """
    context = LexerContext(
        source_filepath=source_filepath,
        lines=lines,
        row_end=len(lines),
    )

    while not context.row_is_consumed():
        context.line = lines[context.row]
        context = yield from _consume_context_from_row_start(context=context)
        context.row += 1

    return context


def _consume_context_from_row_start(context: LexerContext) -> TokenGenerator:
    """Feed context to begin from current context line (row)."""
    context.col = find_word_start(context.line, 0)
    context.col_end = len(context.line)

    while not context.col_is_consumed():
        symbol = context.line[context.col]
        location = context.current_location()

        if not (token := _consume_context_from_symbol(symbol, context, location)):
            return context

        yield token

    return context


def _consume_context_from_symbol(
    symbol: str,
    context: LexerContext,
    location: TokenLocation,
) -> Token | None:
    """Consumes starting from given symbol an token.

    returns None if there is no resulting tokens on line, and context is already switched to the next line
    """
    if symbol == "'":
        return _consume_into_character_token(context, location)

    if symbol == '"':
        return _consume_into_string_token(context, location)

    return _consume_into_token(context, location)


def _consume_into_string_token(context: LexerContext, location: TokenLocation) -> Token:
    """Consume context into string token."""
    string_starts_at = context.col + 1
    if string_starts_at >= context.col_end:
        context.col += 1
        raise LexerUnclosedStringQuoteError(
            open_quote_location=context.current_location(),
        )

    string_ends_at = find_string_end(context.line, string_starts_at)
    if string_ends_at is None:
        context.col += 1
        raise LexerUnclosedStringQuoteError(
            open_quote_location=context.current_location(),
        )

    string_raw = context.line[string_starts_at - 1 : string_ends_at + 1]
    string = context.line[string_starts_at:string_ends_at]

    context.col = find_word_start(context.line, string_ends_at + 1)
    return Token(
        type=TokenType.STRING,
        text=string_raw,
        location=location,
        value=unescape_string(string),
    )


def _consume_number_into_token(word: str, location: TokenLocation) -> Token | None:
    """Try to consume given word into number token (integer / float) or return nothing."""
    if not word.isdigit() and not (word[0] == "-" and word[1:].isdigit()):
        return None
    return Token(
        type=TokenType.INTEGER,
        text=word,
        value=int(word),
        location=location,
    )


def _consume_comment_segment(word: str, context: LexerContext) -> bool:
    """Continues to next line if encountered comment within words."""
    is_comment = word.startswith("//")
    if is_comment:
        context.row += 1
    return is_comment


def _consume_word_or_keyword_into_token(word: str, location: TokenLocation) -> Token:
    """Consume given word into word or keyword according to declaration."""
    if keyword := WORD_TO_KEYWORD.get(word):
        return Token(
            type=TokenType.KEYWORD,
            text=word,
            location=location,
            value=keyword,
        )

    return Token(
        type=TokenType.WORD,
        text=word,
        location=location,
        value=word,
    )


def _consume_into_token(context: LexerContext, location: TokenLocation) -> Token | None:
    """Consumes base symbol into token (non-string, no-character)."""
    word_starts_at = context.col
    word_ends_at = find_word_end(context.line, context.col)

    word = context.line[word_starts_at:word_ends_at]
    context.col = find_word_start(context.line, word_ends_at)

    if _consume_comment_segment(word, context):
        return None

    if token := _consume_number_into_token(word, location):
        return token

    return _consume_word_or_keyword_into_token(word, location)


def _consume_into_character_token(
    context: LexerContext,
    location: TokenLocation,
) -> Token:
    """Consume current context line with resulting character token."""
    char_starts_at = context.col + 1
    char_ends_at = context.line.find("'", char_starts_at)

    if char_ends_at == -1:
        context.col += 1
        raise LexerUnclosedCharacterQuoteError(
            open_quote_location=context.current_location(),
        )

    character_raw = context.line[char_starts_at - 1 : char_ends_at + 1]
    character = character_raw[1:-1]
    character = unescape_string(character)

    character_len = len(character)
    if character_len == 0:
        context.col += 1
        raise LexerEmptyCharacterError(open_quote_location=context.current_location())
    if character_len > 1:
        context.col += 2
        raise LexerExcessiveCharacterLengthError(
            excess_begins_at=context.current_location(),
            excess_by_count=character_len,
        )
    assert character_len == 1

    context.col = find_word_start(context.line, char_ends_at + 1)

    return Token(
        type=TokenType.CHARACTER,
        text=character_raw,
        value=ord(character),
        location=location,
    )
