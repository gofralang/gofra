from gofra.lexer.keywords import WORD_TO_KEYWORD

from .exceptions import (
    LexerAmbiguousSymbolLengthError,
    LexerEmptyInputLinesError,
    LexerEmptySymbolError,
    LexerUnclosedStringQuoteError,
    LexerUnclosedSymbolQuoteError,
)
from .helpers import (
    find_column,
    find_string_end,
    find_word_end,
    find_word_start,
    unescape_string,
)
from .tokens import Token, TokenGenerator, TokenLocation, TokenType


def tokenize_text(lines: list[str], filename: str) -> TokenGenerator:
    idx = 0
    idx_end = len(lines)

    if idx_end == 0:
        raise LexerEmptyInputLinesError

    while idx < idx_end:
        line = lines[idx]

        idy = find_word_start(line, 0)
        idy_end = len(line)

        while idy < idy_end:
            loc = (filename, idx + 1, idy + 1)
            symbol = line[idy]

            match symbol:
                case "'":
                    idy, token = _tokenize_symbol_token(loc, idy, idy_end, line)
                    yield token
                case '"':
                    string = ""

                    string_ends_at = None
                    while idx < idx_end:
                        string_starts_at = idy if string else idy + 1
                        if string:
                            line = lines[idx]
                            idy_end = len(line)

                        string_ends_at = find_string_end(line, string_starts_at)
                        if string_ends_at is None:
                            string += line[string_starts_at:]
                            idx += 1
                            idy = 0
                            continue
                        else:
                            string += line[string_starts_at:string_ends_at]
                            break

                    assert string_ends_at is not None
                    if idx >= idx_end:
                        raise LexerUnclosedStringQuoteError

                    yield Token(
                        type=TokenType.STRING,
                        text=f'"{string}"',
                        location=loc,
                        value=unescape_string(string),
                    )
                    idy = find_word_start(line, string_ends_at + 1)
                case _:
                    word_ends_at = find_word_end(line, idy)
                    word = line[idy:word_ends_at]

                    if word.startswith("//"):
                        # TODO(@kirillzhosul): Split segment and make comments fully supported
                        break

                    if token := _tokenize_number_token(loc, word):
                        idy = find_word_start(line, word_ends_at)
                        yield token
                        continue

                    yield _tokenize_word_token(loc, word)
                    idy = find_word_start(line, word_ends_at)
        idx += 1


def _tokenize_word_token(loc: TokenLocation, word: str) -> Token:
    keyword = WORD_TO_KEYWORD.get(word)

    if keyword:
        return Token(
            type=TokenType.KEYWORD,
            text=word,
            location=loc,
            value=keyword,
        )

    return Token(
        type=TokenType.WORD,
        text=word,
        location=loc,
        value=word,
    )


def _tokenize_number_token(loc: TokenLocation, word: str) -> Token | None:
    if word.isdigit():
        return Token(
            type=TokenType.INTEGER,
            text=word,
            value=int(word),
            location=loc,
        )

    if len(word) == 1:
        return

    if word.replace(".", "", count=1).isdigit():
        value = float("0." + word[1:] if word[0] == "." else word)
        return Token(
            type=TokenType.FLOAT,
            text=word,
            value=value,
            location=loc,
        )


def _tokenize_symbol_token(
    loc: TokenLocation, idy: int, idy_end: int, line: str
) -> tuple[int, Token]:
    symbol_starts_at = idy + 1
    symbol_ends_at = find_column(line, symbol_starts_at, lambda s: s == "'")
    if symbol_ends_at >= idy_end:
        raise LexerUnclosedSymbolQuoteError

    symbol_len = symbol_ends_at - idy - 1
    if symbol_len == 0:
        raise LexerEmptySymbolError
    if symbol_len > 1:
        raise LexerAmbiguousSymbolLengthError

    symbol = unescape_string(line[symbol_starts_at:symbol_ends_at])
    assert len(symbol) == 1

    idy = find_word_start(line, symbol_ends_at + 1)
    token = Token(
        type=TokenType.SYMBOL,
        text=line[symbol_starts_at - 1 : symbol_ends_at + 1],
        location=loc,
        value=symbol,
    )

    return idy, token
