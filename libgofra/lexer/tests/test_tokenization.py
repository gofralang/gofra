"""Tests for the character-driven tokenizer.

The lexer splits source code by character classes (and not by whitespace), so
`a+b` and `a + b` must produce the very same token stream.
"""

import pytest

from libgofra.lexer.errors.invalid_number_literal import InvalidNumberLiteralError
from libgofra.lexer.errors.unknown_preprocessor_directive import (
    UnknownPreprocessorDirectiveError,
)
from libgofra.lexer.errors.unknown_symbol import UnknownSymbolError
from libgofra.lexer.lexer import tokenize_from_raw
from libgofra.lexer.tokens import TokenType


def test_operators_do_not_require_whitespaces() -> None:
    assert_tokens(
        "a+b", [("IDENTIFIER", "a"), ("IDENTIFIER", "+"), ("IDENTIFIER", "b")],
    )
    assert_tokens(
        "a + b", [("IDENTIFIER", "a"), ("IDENTIFIER", "+"), ("IDENTIFIER", "b")],
    )


def test_multi_character_operators_are_munched() -> None:
    assert_tokens(
        "a==b", [("IDENTIFIER", "a"), ("IDENTIFIER", "=="), ("IDENTIFIER", "b")],
    )
    assert_tokens(
        "a!=b", [("IDENTIFIER", "a"), ("IDENTIFIER", "!="), ("IDENTIFIER", "b")],
    )
    assert_tokens(
        "a<=b", [("IDENTIFIER", "a"), ("IDENTIFIER", "<="), ("IDENTIFIER", "b")],
    )
    assert_tokens(
        "a>=b", [("IDENTIFIER", "a"), ("IDENTIFIER", ">="), ("IDENTIFIER", "b")],
    )
    assert_tokens(
        "a&&b", [("IDENTIFIER", "a"), ("IDENTIFIER", "&&"), ("IDENTIFIER", "b")],
    )
    assert_tokens(
        "a||b", [("IDENTIFIER", "a"), ("IDENTIFIER", "||"), ("IDENTIFIER", "b")],
    )
    assert_tokens(
        "a<<b", [("IDENTIFIER", "a"), ("IDENTIFIER", "<<"), ("IDENTIFIER", "b")],
    )
    assert_tokens(
        "a>>b", [("IDENTIFIER", "a"), ("IDENTIFIER", ">>"), ("IDENTIFIER", "b")],
    )
    assert_tokens("x !<", [("IDENTIFIER", "x"), ("IDENTIFIER", "!<")])
    assert_tokens("x ?>", [("IDENTIFIER", "x"), ("IDENTIFIER", "?>")])


def test_assignment_is_a_separate_token() -> None:
    assert_tokens(
        "var x int=5",
        [
            ("KEYWORD", "var"),
            ("IDENTIFIER", "x"),
            ("IDENTIFIER", "int"),
            ("ASSIGNMENT", "="),
            ("INTEGER", "5"),
        ],
    )


def test_ampersand_is_address_of_when_glued() -> None:
    assert_tokens("&x", [("AMPERSAND", "&"), ("IDENTIFIER", "x")])
    assert_tokens("& x", [("AMPERSAND", "&"), ("IDENTIFIER", "x")])


def test_ampersand_adjacency_is_tracked() -> None:
    glued = list(tokenize_from_raw("cli", lines=["&x"]))
    separated = list(tokenize_from_raw("cli", lines=["& x"]))

    assert glued[0].type == TokenType.AMPERSAND
    assert glued[0].has_trailing_whitespace is False
    assert separated[0].type == TokenType.AMPERSAND
    assert separated[0].has_trailing_whitespace is True


def test_dot_dot_is_a_single_token() -> None:
    assert_tokens(
        "0..n",
        [
            ("INTEGER", "0"),
            ("DOT_DOT", ".."),
            ("IDENTIFIER", "n"),
        ],
    )


def test_dot_is_a_separate_token() -> None:
    assert_tokens("a.b", [("IDENTIFIER", "a"), ("DOT", "."), ("IDENTIFIER", "b")])


def test_dot_adjacency_is_tracked() -> None:
    glued = list(tokenize_from_raw("cli", lines=["a.b"]))
    separated = list(tokenize_from_raw("cli", lines=["a . b"]))

    assert glued[1].type == TokenType.DOT
    assert glued[1].has_leading_whitespace is False
    assert glued[1].has_trailing_whitespace is False
    assert separated[1].type == TokenType.DOT
    assert separated[1].has_leading_whitespace is True
    assert separated[1].has_trailing_whitespace is True


def test_negative_number_literal() -> None:
    assert_tokens("-1", [("INTEGER", "-1")])
    assert next(iter(tokenize_from_raw("cli", lines=["-1"]))).value == -1


def test_sign_is_a_part_of_a_number_when_it_is_glued_to_it() -> None:
    # A sign that is directly followed by a digit is always a part of the number literal
    assert_tokens("1-2", [("INTEGER", "1"), ("INTEGER", "-2")])
    assert_tokens("1 -2", [("INTEGER", "1"), ("INTEGER", "-2")])
    # ...while a separated sign is an operator
    assert_tokens("1 - 2", [("INTEGER", "1"), ("IDENTIFIER", "-"), ("INTEGER", "2")])


def test_number_bases() -> None:
    assert next(iter(tokenize_from_raw("cli", lines=["0x1F"]))).value == 31
    assert next(iter(tokenize_from_raw("cli", lines=["0X1f"]))).value == 31
    assert next(iter(tokenize_from_raw("cli", lines=["0b1010"]))).value == 10
    assert next(iter(tokenize_from_raw("cli", lines=["0o777"]))).value == 511


def test_number_with_digit_separators() -> None:
    assert next(iter(tokenize_from_raw("cli", lines=["1_000"]))).value == 1000


def test_number_with_exponent() -> None:
    token = next(iter(tokenize_from_raw("cli", lines=["1.5e3"])))
    assert token.type == TokenType.FLOAT
    assert token.value == 1500.0


def test_malformed_number_raises_diagnostic() -> None:
    with pytest.raises(InvalidNumberLiteralError):
        list(tokenize_from_raw("cli", lines=["0x"]))

    with pytest.raises(InvalidNumberLiteralError):
        list(tokenize_from_raw("cli", lines=["12abc"]))


def test_unknown_symbol_raises_diagnostic() -> None:
    with pytest.raises(UnknownSymbolError):
        list(tokenize_from_raw("cli", lines=["a ~ b"]))


def test_unknown_preprocessor_directive_raises_diagnostic() -> None:
    with pytest.raises(UnknownPreprocessorDirectiveError):
        list(tokenize_from_raw("cli", lines=["#nope"]))


def test_preprocessor_directive_is_a_keyword() -> None:
    assert_tokens(
        "#define X 1", [("KEYWORD", "#define"), ("IDENTIFIER", "X"), ("INTEGER", "1")],
    )


def test_comment_is_skipped() -> None:
    assert_tokens("a // b c", [("IDENTIFIER", "a")])


def test_non_ascii_string_literal() -> None:
    token = next(iter(tokenize_from_raw("cli", lines=['"日本"'])))
    assert token.type == TokenType.STRING
    assert token.value == "日本"


def test_escaped_backslash_in_string() -> None:
    token = next(iter(tokenize_from_raw("cli", lines=[r'"a\\"'])))
    assert token.type == TokenType.STRING
    assert token.value == "a\\"


def test_escaped_quote_in_string() -> None:
    token = next(iter(tokenize_from_raw("cli", lines=[r'"\""'])))
    assert token.type == TokenType.STRING
    assert token.value == '"'


def test_cli_source_does_not_loop_forever() -> None:
    # A single symbol token used to reset the cursor back and cause an infinite loop
    tokens = list(tokenize_from_raw("cli", lines=["a = b"]))
    assert [token.type for token in tokens] == [
        TokenType.IDENTIFIER,
        TokenType.ASSIGNMENT,
        TokenType.IDENTIFIER,
        TokenType.EOL,
        TokenType.EOF,
    ]


def assert_tokens(source: str, expected: list[tuple[str, str]]) -> None:
    tokens = [
        (token.type.name, token.text)
        for token in tokenize_from_raw("cli", lines=[source])
        if token.type not in (TokenType.EOL, TokenType.EOF)
    ]
    assert tokens == expected
