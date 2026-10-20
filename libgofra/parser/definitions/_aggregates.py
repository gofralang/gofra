from libgofra.lexer import Keyword, TokenType
from libgofra.lexer.tokens import TokenLocation
from libgofra.parser._context import ParserContext
from libgofra.parser.errors.wildcard_cannot_be_used_as_symbol_name import (
    WildcardCannotBeUsedAsSymbolNameError,
)
from libgofra.parser.type_parser import parse_concrete_type_from_tokenizer
from libgofra.types import Type
from libgofra.types.composite import StructureType, UnionType


def parse_aggregate_definition_members(
    context: ParserContext,
    aggregate: StructureType | UnionType,
) -> tuple[list[tuple[str, Type]], bool]:
    members = []

    references_self = False
    while token := context.next_token():
        if token.type == TokenType.KEYWORD and token.value == Keyword.END:
            break

        field_name_token = token
        if field_name_token.type != TokenType.IDENTIFIER:
            msg = f"Expected field/member name as identifier but got {field_name_token.type.name} at {field_name_token.location}"
            raise ValueError(msg)

        member_name = field_name_token.text
        member_type = parse_concrete_type_from_tokenizer(context)
        if id(member_type) == id(aggregate):
            references_self = True

        members.append((member_name, member_type))
    return members, references_self


def validate_aggregate_name_redefinition(
    scope: ParserContext,
    name: str,
    defined_at: TokenLocation,
) -> None:
    if name == "_":
        raise WildcardCannotBeUsedAsSymbolNameError(at=defined_at)

    if scope.scope.lookup(name):
        msg = f"Aggregate at {defined_at} with name {name} is already taken by other definition"
        raise ValueError(msg)
