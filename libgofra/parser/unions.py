from typing import TYPE_CHECKING

from libgofra.exceptions import GofraError
from libgofra.lexer.keywords import Keyword
from libgofra.lexer.tokens import TokenType
from libgofra.parser._context import ParserScope
from libgofra.parser.errors.wildcard_cannot_be_used_as_symbol_name import (
    WildcardCannotBeUsedAsSymbolNameError,
)
from libgofra.parser.type_parser import (
    consume_generic_type_parameters,
    parse_concrete_type_from_tokenizer,
)
from libgofra.types.composite.union import UnionType

if TYPE_CHECKING:
    from libgofra.types._base import Type


def unpack_union_definition_from_token(context: ParserScope) -> None:
    name_token = context.next_token()
    if name_token.type != TokenType.IDENTIFIER:
        msg = f"Expected union name at {name_token.location} to be an identifier but got {name_token.type.name}"
        raise ValueError(msg)

    name = name_token.text
    if name == "_":
        raise WildcardCannotBeUsedAsSymbolNameError(at=name_token.location)

    if context.query_name_holder(name):
        msg = f"Union name {name} is already taken by other definition"
        raise ValueError(msg)
    if (
        context.peek_token().type == TokenType.LCURLY
        and not context.peek_token().has_trailing_whitespace
    ):
        _ = consume_generic_type_parameters(context)
        msg = "Generic unions not available yet"
        raise GofraError(msg)
        return

    _consume_concrete_union_type_definition(
        context,
        name,
    )


def _consume_concrete_union_type_definition(
    context: ParserScope,
    name: str,
) -> None:
    # Forward declare this union so users may use that type in union definition
    # this must to be back-patched after parsing types
    ref = UnionType(
        name=name,
        members={},
    )
    assert name not in context.types
    context.types[name] = ref

    members: dict[str, Type] = {}

    while token := context.next_token():
        if token.type == TokenType.KEYWORD and token.value == Keyword.END:
            # End of structure block definition
            break
        field_name_token = token

        if field_name_token.type != TokenType.IDENTIFIER:
            msg = f"Expected structure field name at {field_name_token.location} to be an identifier but got {field_name_token.type.name}"
            raise ValueError(msg)
        member_name = field_name_token.text
        member_type = parse_concrete_type_from_tokenizer(context)
        if id(member_type) == id(ref):
            msg = f"Cannot reference self union in union at {token.location}"
            raise GofraError(msg)

        members[member_name] = member_type

    ref.backpatch(members)

    for member_type in ref.members.values():
        if member_type.size_in_bytes == 0:
            msg = f"zero sized member at {token.location}"
            raise GofraError(msg)

    if not ref.members:
        msg = f"no members for union at {token.location}"
        raise GofraError(msg)

    if ref.size_in_bytes <= 0:
        msg = f"zero size union at {token.location}"
        raise GofraError(msg)
