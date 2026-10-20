from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from libgofra.lexer.keywords import Keyword
from libgofra.lexer.tokens import Token, TokenType
from libgofra.parser._context import ParserContext
from libgofra.parser.definitions._aggregates import (
    parse_aggregate_definition_members,
    validate_aggregate_name_redefinition,
)
from libgofra.parser.errors.structure_field_has_zero_size import (
    StructureFieldHasZeroError,
)
from libgofra.parser.errors.structure_has_no_fields import StructureHasNoFieldsError
from libgofra.parser.errors.structure_has_zero_size import StructureHasZeroSizeError
from libgofra.parser.type_parser import (
    consume_generic_type_parameters,
    parse_generic_type_alias_from_tokenizer,
)
from libgofra.types.composite.structure import StructureType
from libgofra.types.generics import GenericParametrizedType, GenericStructureType

if TYPE_CHECKING:
    from libgofra.types._base import Type


@dataclass
class _StructureSpec:
    name: str
    is_packed: bool
    reorder: bool
    token: Token


def parse_structure_definition(context: ParserContext) -> None:
    """Parse and define structure (as type) starting from name token."""
    spec = _parse_structure_spec(context)
    validate_aggregate_name_redefinition(context, spec.name, spec.token.location)

    if context.peek_token().type == TokenType.LCURLY:
        type_params = consume_generic_type_parameters(context)
        _parse_generic_structure_definition(context, spec, type_params=type_params)
        return

    _parse_concrete_structure_definition(context, spec)


def _parse_structure_spec(context: ParserContext) -> _StructureSpec:
    attr_is_packed, attr_reorder = False, False

    while context.peek_token().type == TokenType.KEYWORD:
        attr_token = context.next_token()
        assert attr_token.type == TokenType.KEYWORD
        match attr_token.value:
            case Keyword.ATTR_STRUCT_PACKED:
                assert not attr_is_packed, attr_token.location
                attr_is_packed = True
            case Keyword.ATTR_STRUCT_REORDER:
                assert not attr_reorder, attr_token.location
                attr_reorder = True
            case _:
                raise ValueError(attr_token)

    context.expect_token(TokenType.IDENTIFIER)
    name_token = context.next_token()

    name = name_token.text
    return _StructureSpec(
        name,
        attr_is_packed,
        attr_reorder,
        token=name_token,
    )


def _parse_generic_structure_definition(
    context: ParserContext,
    spec: _StructureSpec,
    type_params: Mapping[str, Token],
) -> None:
    # Forward declare this struct so users may use that type in structure definition
    # this must to be back-patched after parsing types

    ref = GenericStructureType(
        name=spec.name,
        fields={},
        fields_ordering=[],
        is_packed=spec.is_packed,
        reorder=spec.reorder,
    )
    context.scope.declare_type(spec.name, ref)

    fields: dict[str, Type | GenericParametrizedType] = {}
    fields_ordering: list[str] = []

    while token := context.next_token():
        if token.type == TokenType.KEYWORD and token.value == Keyword.END:
            # End of structure block definition
            break
        field_name_token = token

        if field_name_token.type != TokenType.IDENTIFIER:
            msg = f"Expected structure field name at {field_name_token.location} to be an identifier but got {field_name_token.type.name}"
            raise ValueError(msg)
        field_name = field_name_token.text
        field_type = parse_generic_type_alias_from_tokenizer(
            context,
            generic_type_params=type_params,
        )
        fields_ordering.append(field_name)
        fields[field_name] = field_type

    # Back-patch reference
    ref.fields = fields
    ref.fields_ordering = fields_ordering


def _parse_concrete_structure_definition(
    context: ParserContext,
    spec: _StructureSpec,
) -> None:
    # Forward declare this struct so users may use that type in structure definition
    # this must to be back-patched after parsing types
    ref = StructureType(
        name=spec.name,
        fields={},
        order=[],
        is_packed=spec.is_packed,
        reorder=spec.reorder,
    )
    context.scope.declare_type(spec.name, ref)

    members_flat, references_self = parse_aggregate_definition_members(context, ref)

    # Back-patch reference
    ref.backpatch(
        fields=dict(members_flat),
        order=[k for k, _ in members_flat],
        # TODO: proper backpatch
        has_forward_reference=references_self,
    )

    for field_name, field_type in ref.natural_fields.items():
        if field_type.size_in_bytes == 0:
            at = context.peek_token().location
            raise StructureFieldHasZeroError(
                field_type=field_type,
                field_name=field_name,
                at=at,
                structure=ref,
            )

    if not ref.natural_fields:
        at = context.peek_token().location
        raise StructureHasNoFieldsError(structure=ref, at=at)

    if ref.size_in_bytes <= 0:
        at = context.peek_token().location
        raise StructureHasZeroSizeError(structure=ref, at=at)
