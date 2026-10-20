from dataclasses import dataclass

from libgofra.exceptions import GofraError
from libgofra.lexer import Token
from libgofra.lexer.tokens import TokenType
from libgofra.parser._context import ParserContext
from libgofra.types.composite.union import UnionType

from ._aggregates import (
    parse_aggregate_definition_members,
    validate_aggregate_name_redefinition,
)


# TODO: union attributes
#
@dataclass
class _UnionSpec:
    name: str
    token: Token


def parse_union_definition(context: ParserContext) -> None:
    """Parse and define union (as type) starting from name token."""
    spec = _parse_union_spec(context)
    validate_aggregate_name_redefinition(context, spec.name, spec.token.location)

    if context.peek_token().type == TokenType.LCURLY:
        msg = "Generic unions not available yet"
        raise NotImplementedError(msg)
    else:  # noqa: RET506
        # Forward declare this union so users may use that type in union definition
        # this must to be back-patched after parsing types
        ref = UnionType(name=spec.name, members={})
        context.scope.declare_type(spec.name, ref)

        members_flat, references_self = parse_aggregate_definition_members(context, ref)
        if references_self:
            msg = f"Self reference union at {spec.token.location}"
            raise ValueError(msg)

        ref.backpatch(members=dict(members_flat))

        for member_type in ref.members.values():
            if member_type.size_in_bytes == 0:
                msg = f"Zero sized member at {spec.token.location}"
                raise GofraError(msg)

        if not ref.members:
            msg = f"No members for union at {spec.token.location}"
            raise GofraError(msg)

        if ref.size_in_bytes <= 0:
            msg = f"Zero size union at {spec.token.location}"
            raise GofraError(msg)


def _parse_union_spec(scope: ParserContext) -> _UnionSpec:
    scope.expect_token(TokenType.IDENTIFIER)
    name_token = scope.next_token()

    name = name_token.text
    return _UnionSpec(name=name, token=name_token)
