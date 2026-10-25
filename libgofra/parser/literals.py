from typing import TYPE_CHECKING

from libgofra.hir.literals import (
    ArrayLiteral,
    BooleanLiteral,
    CharacterLiteral,
    FloatLiteral,
    IntegerLiteral,
    Literal_T,
    StringLiteral,
    StructureLiteral,
)
from libgofra.lexer import Keyword
from libgofra.lexer.tokens import TokenType
from libgofra.parser._context import ParserContext

if TYPE_CHECKING:
    from collections.abc import MutableMapping


def parse_integer_literal(context: ParserContext) -> IntegerLiteral:
    context.expect_token(TokenType.INTEGER)
    token = context.next_token()

    assert isinstance(token.value, int)
    return IntegerLiteral(token, token.value)


def parse_float_literal(context: ParserContext) -> FloatLiteral:
    context.expect_token(TokenType.FLOAT)
    token = context.next_token()

    assert isinstance(token.value, float)
    return FloatLiteral(token, token.value)


def parse_array_literal(context: ParserContext) -> ArrayLiteral:
    context.expect_token(TokenType.LBRACKET)
    start_token = context.next_token()

    elements: list[Literal_T] = []
    default: Literal_T | None = None
    while True:
        if context.peek_token().type == TokenType.RBRACKET:
            context.advance_token()
            break

        elements.append(parse_any_literal(context))

        if context.peek_token().type == TokenType.RBRACKET:
            context.advance_token()
            break

        if context.peek_token().type == TokenType.SEMICOLON:
            context.advance_token()
            context.expect_token(TokenType.INTEGER)
            default = parse_any_literal(context)
            context.expect_token(TokenType.RBRACKET)
            break

        context.expect_token(TokenType.COMMA)
        context.advance_token()
    return ArrayLiteral(token=start_token, elements=elements, default=default)


def parse_character_literal(context: ParserContext) -> CharacterLiteral:
    context.expect_token(TokenType.CHARACTER)
    token = context.next_token()

    assert isinstance(token.value, int)
    return CharacterLiteral(token, token.value)


def parse_boolean_literal(context: ParserContext) -> BooleanLiteral:
    token = context.next_token()
    if token.type == TokenType.INTEGER:
        assert isinstance(token.value, int)
        if token.value not in (0, 1):
            msg = f"Value for boolean must be in two states: 0 or 1, but got {token.value} at {token.location}"
            raise ValueError(msg)
        return BooleanLiteral(token, bool(token.value))

    if token.type == TokenType.KEYWORD and token.value in (Keyword.TRUE, Keyword.FALSE):
        return BooleanLiteral(token, token.value == Keyword.TRUE)

    msg = f"Expected BOOLEAN literal but got {token.type.name} at {token.location}"
    raise ValueError(msg)


def parse_structure_literal(context: ParserContext) -> StructureLiteral:
    context.expect_token((TokenType.LCURLY, TokenType.IDENTIFIER))
    start_token = context.next_token()

    name = None
    if start_token.type == TokenType.IDENTIFIER:
        name = start_token.text
        context.expect_token(TokenType.LCURLY)
        context.advance_token()

    fields: MutableMapping[str, Literal_T] = {}
    while token := context.peek_token():
        if token.type == TokenType.RCURLY:
            context.advance_token()
            break
        context.expect_token(TokenType.IDENTIFIER)
        field_name = context.next_token().text

        context.expect_token(TokenType.ASSIGNMENT)
        context.advance_token()

        fields[field_name] = parse_any_literal(context)

        if context.peek_token().type == TokenType.RCURLY:
            context.advance_token()
            break

        context.expect_token(TokenType.COMMA)
        context.advance_token()

    return StructureLiteral(token=start_token, name=name, fields=fields)


def parse_string_literal(context: ParserContext) -> StringLiteral:
    token = context.next_token()
    if token.type != TokenType.STRING:
        msg = f"Expected STRING literal, but got {token.type.name} at {token.location}"
        raise ValueError(msg)

    string_raw = str(token.text[1:-1])
    return StringLiteral(token=token, value=string_raw)


def parse_any_literal(context: ParserContext) -> Literal_T:  # noqa: PLR0911
    token = context.peek_token()
    if token.type == TokenType.INTEGER:
        return parse_integer_literal(context)
    if token.type == TokenType.FLOAT:
        return parse_float_literal(context)
    if token.type == TokenType.CHARACTER:
        return parse_character_literal(context)
    if token.type == TokenType.LBRACKET:
        return parse_array_literal(context)
    if token.type == TokenType.LCURLY or (
        token.type == TokenType.IDENTIFIER
        and context.peek_token(n=1).type == TokenType.LCURLY
    ):
        return parse_structure_literal(context)
    if token.type == TokenType.KEYWORD and token.value in (Keyword.TRUE, Keyword.FALSE):
        return parse_boolean_literal(context)
    if token.type == TokenType.STRING:
        return parse_string_literal(context)

    msg = f"Expected literal but got {token.type.name} at {token.location}"
    raise ValueError(msg)
