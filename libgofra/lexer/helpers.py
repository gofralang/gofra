from __future__ import annotations

from typing import TYPE_CHECKING

from libgofra.lexer.errors.invalid_escape_sequence import InvalidEscapeSequenceError

if TYPE_CHECKING:
    from libgofra.lexer.tokens import TokenLocation


ESCAPE_SYMBOL = "\\"

HEX_DIGITS = "0123456789abcdefABCDEF"
OCTAL_DIGITS = "01234567"

# Escape sequences that are replaced with a single symbol
SIMPLE_ESCAPE_SEQUENCES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "0": "\0",
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "v": "\v",
    "\\": "\\",
    "'": "'",
    '"': '"',
}


def find_quoted_literal_end(line: str, idx: int, *, quote: str) -> int:
    r"""Find index where given quoted literal ends (right after the close quote).

    Escape sequences are respected, so `"a\\\\"` is a properly closed literal
    (containing a single backslash) and `"\\""` is a properly closed literal
    (containing a single quote).

    :returns: Index right after the close quote or -1 if literal is not closed.
    """
    idx_end = len(line)

    while idx < idx_end:
        current = line[idx]
        if current == ESCAPE_SYMBOL:
            # Skip the escape symbol along with the symbol it escapes
            idx += 2
            continue
        if current == quote:
            return idx + 1
        idx += 1

    return -1


def unescape_text_literal(text: str, *, at: TokenLocation) -> str:
    r"""Replace escape sequences within string/char literal body with real symbols.

    Supported escape sequences: `\\n` `\\t` `\\r` `\\0` `\\a` `\\b` `\\f` `\\v`
    `\\\\` `\\'` `\\"` `\\xNN` `\\uNNNN` `\\UNNNNNNNN` `\\NNN` (octal).

    :raises InvalidEscapeSequenceError: Encountered an unknown or malformed escape sequence.
    """
    result: list[str] = []
    idx = 0
    length = len(text)

    while idx < length:
        current = text[idx]
        if current != ESCAPE_SYMBOL:
            result.append(current)
            idx += 1
            continue

        if idx + 1 >= length:
            raise InvalidEscapeSequenceError(at=at, sequence=ESCAPE_SYMBOL)

        escaped = text[idx + 1]

        if simple := SIMPLE_ESCAPE_SEQUENCES.get(escaped):
            result.append(simple)
            idx += 2
            continue

        if escaped in ("x", "u", "U"):
            expected = {"x": 2, "u": 4, "U": 8}[escaped]
            digits = text[idx + 2 : idx + 2 + expected]
            if len(digits) != expected or not all(d in HEX_DIGITS for d in digits):
                raise InvalidEscapeSequenceError(
                    at=at,
                    sequence=text[idx : idx + 2 + expected],
                )
            result.append(chr(int(digits, 16)))
            idx += 2 + expected
            continue

        if escaped in OCTAL_DIGITS:
            digits = ""
            cursor = idx + 1
            while cursor < length and len(digits) < 3 and text[cursor] in OCTAL_DIGITS:
                digits += text[cursor]
                cursor += 1
            result.append(chr(int(digits, 8)))
            idx = cursor
            continue

        raise InvalidEscapeSequenceError(at=at, sequence=text[idx : idx + 2])

    return "".join(result)
