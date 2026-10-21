"""Consistency checks between the lexical symbol table and the parser operator table.

The lexer knows *how* a symbol is spelled (and how long it is), the parser knows *what*
it means. Both tables must agree, otherwise an operator would either be lexed into
multiple tokens or would be unknown to the parser.
"""

from libgofra.lexer.symbols import (
    KNOWN_SYMBOLS,
    OPERATOR_SYMBOLS,
    STRUCTURAL_SYMBOL_TO_TOKEN_TYPE,
)
from libgofra.parser.operators import IDENTIFIER_TO_OPERATOR_TYPE

# "*" is lexed as a dedicated token (TokenType.STAR) - it is both a pointer type sigil
# and a multiplication operator, so the lexer cannot emit it as an operator spelling.
SYMBOLS_WITH_DEDICATED_TOKEN_TYPE = frozenset(STRUCTURAL_SYMBOL_TO_TOKEN_TYPE)


def test_every_operator_symbol_is_known_to_the_parser() -> None:
    unknown = OPERATOR_SYMBOLS - IDENTIFIER_TO_OPERATOR_TYPE.keys()
    assert not unknown, f"Operator symbols unknown to the parser: {sorted(unknown)}"


def test_every_parser_operator_is_lexable() -> None:
    for spelling in IDENTIFIER_TO_OPERATOR_TYPE:
        if spelling in KNOWN_SYMBOLS:
            continue
        # Not a symbol - it must be lexable as a plain word (e.g `lnot`)
        assert spelling.isidentifier(), (
            f"Operator '{spelling}' is neither a known symbol nor a valid identifier"
        )


def test_symbols_with_dedicated_token_type_are_not_operators() -> None:
    for symbol in SYMBOLS_WITH_DEDICATED_TOKEN_TYPE:
        if symbol == "*":
            # Multiplication is handled by the parser as a dedicated token type
            continue
        assert symbol not in IDENTIFIER_TO_OPERATOR_TYPE, (
            f"Symbol '{symbol}' has a dedicated token type and must not be an operator"
        )
