"""Lexical table of symbol spellings that lexer knows about.

This table is purely **lexical**: it tells which character sequences are a single symbol
and how long they are. Semantic meaning of an operator (e.g `+` -> `ARITHMETIC_PLUS`)
lives in the parser (`libgofra/parser/operators.py`) and is not duplicated here.

Operator spellings are emitted by the lexer as `IDENTIFIER` tokens (with the spelling as
a text), so the parser keeps resolving them via its own table.
"""

from libgofra.lexer.tokens import TokenType

# Multi-character symbols. Must be sorted by length (descending) for maximal munch.
MULTI_CHARACTER_SYMBOLS = (
    "==",
    "!=",
    "<=",
    ">=",
    "&&",
    "||",
    "<<",
    ">>",
    "!<",
    "?>",
    "..",
)

# Single-character symbols.
# NOTE: "!" is not here on purpose - it is only valid as a part of "!=" or "!<"
SINGLE_CHARACTER_SYMBOLS = (
    "+",
    "-",
    "*",
    "/",
    "%",
    "<",
    ">",
    "=",
    "&",
    "|",
    "^",
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
    ",",
    ";",
    ":",
    ".",
)

KNOWN_SYMBOLS = frozenset(MULTI_CHARACTER_SYMBOLS + SINGLE_CHARACTER_SYMBOLS)

# Symbols that have a dedicated token type. Everything else that is not listed here
# is emitted as an `IDENTIFIER` token (operator spelling).
STRUCTURAL_SYMBOL_TO_TOKEN_TYPE: dict[str, TokenType] = {
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    "{": TokenType.LCURLY,
    "}": TokenType.RCURLY,
    ",": TokenType.COMMA,
    ";": TokenType.SEMICOLON,
    ":": TokenType.COLON,
    ".": TokenType.DOT,
    "..": TokenType.DOT_DOT,
    "=": TokenType.ASSIGNMENT,
    "*": TokenType.STAR,
    "&": TokenType.AMPERSAND,
}

# Operator spellings that are emitted as `IDENTIFIER` tokens (resolved by the parser).
OPERATOR_SYMBOLS = frozenset(KNOWN_SYMBOLS - set(STRUCTURAL_SYMBOL_TO_TOKEN_TYPE))


def match_symbol_at(text: str, col: int) -> str | None:
    """Match the longest known symbol that starts at given column.

    :returns: Symbol spelling or None if there is no known symbol at that position.
    """
    for length in (2, 1):
        candidate = text[col : col + length]
        if candidate in KNOWN_SYMBOLS:
            return candidate
    return None
