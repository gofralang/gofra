from collections.abc import Mapping, Sequence
from typing import cast

from libgofra.feature_flags import FEATURE_ALLOW_SLICES
from libgofra.hir.function import FunctionParameter
from libgofra.lexer.keywords import Keyword
from libgofra.lexer.tokens import Token, TokenType
from libgofra.parser._context import ParserScope
from libgofra.parser.errors.unknown_primitive_type import UnknownPrimitiveTypeError
from libgofra.parser.functions.exceptions import ParserFunctionNoNameError
from libgofra.types import Type
from libgofra.types.composite.array import ArrayType
from libgofra.types.composite.function import FunctionType
from libgofra.types.composite.pointer import PointerType
from libgofra.types.composite.slice import SliceType
from libgofra.types.generics import (
    GenericArrayType,
    GenericFunctionType,
    GenericParameter,
    GenericParametrizedType,
    GenericPointerType,
    apply_generic_type_into_concrete,
    get_generic_type_parameters_count,
)


# TODO(@kirillzhosul): deep pointer is not allowed
# TODO(@kirillzhosul): distinguish array-of-pointers and pointer-to-array
# TODO(@kirillzhosul): Type parsing is weird (especially new allow_inferring_variable_types) must be separated in complex-type parsing system ?
def parse_concrete_type_from_tokenizer(
    context: ParserScope,
    *,
    allow_inferring_variable_types: bool = False,
) -> Type:
    """Obtain concrete specialized type from parser/lexer.

    For concrete types only substitution (e.g application) of generic is allowed.
    Cannot define another generic type.
    """
    pt = context.peek_token()
    if pt.type == TokenType.STAR:
        return _parse_pointer_type(context)

    if pt.type == TokenType.KEYWORD and pt.value == Keyword.FUNCTION:
        return _parse_function_type(context)

    if pt.type == TokenType.LBRACKET:
        return _parse_slice_type(
            context,
            allow_inferring_variable_types=allow_inferring_variable_types,
        )

    context.expect_token(TokenType.IDENTIFIER)
    t = context.next_token()

    aggregated_type: Type | GenericParametrizedType | None = context.get_type(t.text)
    if isinstance(aggregated_type, GenericParametrizedType):
        type_params = consume_concrete_generic_type_parameters(context)
        params_required = get_generic_type_parameters_count(aggregated_type)

        if params_required != len(type_params):
            msg = f"Incompatible type params amount for generic type {t.text} at {t.location}. Expected {params_required} but got {len(type_params)}"
            raise ValueError(msg)
        return apply_generic_type_into_concrete(aggregated_type, type_params)

    if not aggregated_type:
        # Unable to get from primitive registry - probably an structure type definition
        aggregated_type = context.get_struct(t.text)

    if allow_inferring_variable_types and not aggregated_type:
        variable = context.search_variable_in_context_parents(t.text)
        if variable:
            aggregated_type = variable.type

    if not aggregated_type:
        raise UnknownPrimitiveTypeError(t.text, t.location)

    if context.peek_token().type == TokenType.LBRACKET:
        aggregated_type = _parse_array_suffixes(
            context,
            base=aggregated_type,
            generic_params=None,
        )
        assert isinstance(aggregated_type, ArrayType)

    return aggregated_type


def _parse_pointer_type(context: ParserScope) -> PointerType:
    assert context.peek_token().type == TokenType.STAR  # Must be an pointer
    context.advance_token()
    inner_type = parse_concrete_type_from_tokenizer(
        context,
        allow_inferring_variable_types=False,
    )
    return PointerType(points_to=inner_type)


def _parse_slice_type(
    context: ParserScope,
    *,
    allow_inferring_variable_types: bool = False,
) -> SliceType:
    """Parse `[]T`."""
    if not FEATURE_ALLOW_SLICES:
        msg = "Slices feature is not enabled, currently being work-in-progress"
        raise ValueError(msg)
    context.expect_token(TokenType.LBRACKET)
    context.advance_token()  # consume [
    context.expect_token(TokenType.RBRACKET)
    context.advance_token()  # consume ]

    element_type = parse_concrete_type_from_tokenizer(
        context,
        allow_inferring_variable_types=allow_inferring_variable_types,
    )
    return SliceType(element_type=element_type)


def _parse_array_suffixes(
    context: ParserScope,
    base: Type | GenericParametrizedType,
    *,
    generic_params: Mapping[str, Token] | None = None,
) -> Type | GenericParametrizedType:
    """Parse `[N][M]...` suffixes after a base type.

    C-style nesting:  int[3][4]  →  Array(Array(int, 4), 3)
    Supports unsized `[]` (elements_count = 0).
    Supports generic value params: `[N]` when N is in `generic_params`.
    """
    dimensions: list[int | GenericParameter] = []

    while context.peek_token().type == TokenType.LBRACKET:
        context.advance_token()  # consume [
        dimensions.append(
            _parse_array_size_qualifier(context, generic_params=generic_params),
        )

    for dim in reversed(dimensions):
        if isinstance(dim, GenericParameter):
            base = GenericArrayType(element_type=base, element_count=dim)
        else:
            assert isinstance(base, Type)
            base = ArrayType(element_type=base, elements_count=dim)

    return base


def _parse_array_size_qualifier(
    context: ParserScope,
    *,
    generic_params: Mapping[str, Token] | None = None,
) -> int | GenericParameter:
    """Parse one `[N]`, `[]`, or `[T]` (generic value param).

    Returns int for concrete size (0 = unsized), or GenericParameter for `[T]`.
    """
    token = context.next_token()

    if token.type == TokenType.RBRACKET:
        return 0  # unsized: int[]

    if token.type == TokenType.INTEGER:
        assert isinstance(token.value, int)
        size = token.value
        context.expect_token(TokenType.RBRACKET)
        _ = context.next_token()
        return size

    if token.type == TokenType.IDENTIFIER:
        name = token.text
        if generic_params is None or name not in generic_params:
            msg = (
                f"Identifier '{name}' in array size is not a generic type param "
                f"at {token.location}"
            )
            raise ValueError(msg)
        context.expect_token(TokenType.RBRACKET)
        _ = context.next_token()
        return GenericParameter(
            name=name,
            kind=GenericParameter.Kind.VALUE_PARAM,
        )

    msg = (
        f"Expected RBRACKET, INTEGER, or generic param identifier "
        f"in array size, got {token.type.name} at {token.location}"
    )
    raise ValueError(msg)


def _parse_function_type(context: ParserScope) -> FunctionType:
    assert context.peek_token().type == TokenType.KEYWORD
    assert context.peek_token().value == Keyword.FUNCTION
    _, function_params, function_return_type = consume_concrete_function_signature(
        context,
        token=context.next_token(),
    )

    return FunctionType(
        return_type=function_return_type,
        parameter_types=[p.type for p in function_params],
    )


def consume_concrete_function_signature(
    context: ParserScope,
    token: Token,
) -> tuple[str, list[FunctionParameter], Type]:
    """Consume parser context into function signature assuming given token is `function` keyword.

    Returns function name and signature types (`in` and `out).
    """
    return_type = parse_concrete_type_from_tokenizer(context)

    name_token = context.next_token()

    if not name_token:
        raise ParserFunctionNoNameError(token=token)
    if name_token.type != TokenType.IDENTIFIER:
        msg = f"Expected function name in signature but got {name_token.type.name} at {name_token.location}"
        raise ValueError(msg)
    function_name = name_token.text
    parameters = parse_function_type_parameters(context)

    return function_name, parameters, return_type


def consume_type_function_signature(
    context: ParserScope,
    token: Token,
    generic_type_params: Mapping[str, Token],
) -> tuple[
    str,
    list[tuple[str, Type | GenericParametrizedType]],
    Type | GenericParametrizedType,
]:
    """Consume parser context into generic | concrete function signature assuming given token is `function` keyword.

    Although, gofra does not have generic functions now - this parser consumes generic functions for type system(!)

    Returns function name and signature types (`in` and `out`).
    """
    return_type = parse_generic_type_alias_from_tokenizer(
        context,
        generic_type_params=generic_type_params,
    )

    name_token = context.next_token()

    if not name_token:
        raise ParserFunctionNoNameError(token=token)
    if name_token.type != TokenType.IDENTIFIER:
        msg = f"Expected function name in signature but got {name_token.type.name} at {name_token.location}"
        raise ValueError(msg)
    function_name = name_token.text
    parameters = parse_generic_function_type_parameters(
        context,
        generic_type_params=generic_type_params,
    )

    return function_name, parameters, return_type


def parse_generic_function_type_parameters(
    context: ParserScope,
    generic_type_params: Mapping[str, Token],
) -> list[tuple[str, Type | GenericParametrizedType]]:
    # TODO: Refactor with `parse_function_parameters`, same functions except generic type
    parameters: list[tuple[str, Type | GenericParametrizedType]] = []

    if (paren_token := context.next_token()) and paren_token.type != TokenType.LBRACKET:
        msg = f"Expected LBRACKET `[` after function name for parameters but got {paren_token.type.name}"
        raise ValueError(msg, paren_token.location)

    while token := context.peek_token():
        if token.type == TokenType.RBRACKET:
            break
        parameters.append(
            (
                "",
                parse_generic_type_alias_from_tokenizer(
                    context,
                    generic_type_params=generic_type_params,
                ),
            ),
        )
        t = context.peek_token()
        if t.type == TokenType.RBRACKET:
            break
        if t.type == TokenType.IDENTIFIER:
            parameters[-1] = (t.text, parameters[-1][1])
            context.next_token()
            if context.peek_token().type == TokenType.RBRACKET:
                break
        context.expect_token(TokenType.COMMA)
        _ = context.next_token()
    _ = context.next_token()
    return parameters


def parse_function_type_parameters(
    context: ParserScope,
) -> list[FunctionParameter]:
    parameters: list[FunctionParameter] = []

    if (paren_token := context.next_token()) and paren_token.type != TokenType.LBRACKET:
        msg = f"Expected LBRACKET `[` after function name for parameters but got {paren_token.type.name}"
        raise ValueError(msg, paren_token.location)

    while token := context.peek_token():
        if token.type == TokenType.RBRACKET:
            break

        var_t = parse_concrete_type_from_tokenizer(context)

        context.expect_token(TokenType.IDENTIFIER)
        t = context.next_token()

        parameters.append(FunctionParameter(t.text, var_t))

        if context.peek_token().type == TokenType.COMMA:
            _ = context.next_token()  # Next

        elif context.peek_token().type == TokenType.RBRACKET:
            break  # Finished decl

    _ = context.next_token()

    return parameters


def parse_generic_type_alias_from_tokenizer(
    context: ParserScope,
    *,
    generic_type_params: Mapping[str, Token],
) -> Type | GenericParametrizedType:
    if generic_type_params:
        for generic_type_param in generic_type_params.values():
            if context.query_name_holder(generic_type_param.text):
                msg = f"Generic type param '{generic_type_param.text}' name is already taken by other definition at {generic_type_param.location}"
                raise ValueError(msg)

    if context.peek_token().type == TokenType.STAR:
        context.advance_token()
        points_to = parse_generic_type_alias_from_tokenizer(
            context,
            generic_type_params=generic_type_params,
        )

        if isinstance(points_to, GenericParametrizedType):
            return GenericPointerType(points_to=points_to)

        return PointerType(points_to=points_to)

    if (
        context.peek_token().type == TokenType.KEYWORD
        and context.peek_token().value == Keyword.FUNCTION
    ):
        _token = context.next_token()
        _, function_params, function_return_type = consume_type_function_signature(
            context,
            token=_token,
            generic_type_params=generic_type_params,
        )

        anonymous_function_params = [t for _, t in function_params]
        has_generic_parametrized_param = any(
            isinstance(p, GenericParametrizedType) for p in anonymous_function_params
        )
        if (
            isinstance(function_return_type, GenericParametrizedType)
            or has_generic_parametrized_param
        ):
            return GenericFunctionType(
                return_value=function_return_type,
                parameters=anonymous_function_params,
            )
        anonymous_function_params = cast(
            "Sequence[Type]",
            anonymous_function_params,
        )  # Unsafe, but we check above
        return FunctionType(
            return_type=function_return_type,
            parameter_types=anonymous_function_params,
        )
    context.expect_token(TokenType.IDENTIFIER)
    token = context.next_token()
    typename = token.text

    base_t: Type | GenericParametrizedType | None
    base_t = context.get_type(typename) or context.get_struct(typename)

    if typename in generic_type_params:
        base_t = GenericParameter(
            name=typename,
            kind=GenericParameter.Kind.TYPE_PARAM,
        )

    if not base_t:
        raise UnknownPrimitiveTypeError(typename, token.location)

    if context.peek_token().type == TokenType.LBRACKET:
        base_t = _parse_array_suffixes(
            context,
            base_t,
            generic_params=generic_type_params,
        )

    return base_t


def consume_concrete_generic_type_parameters(
    context: ParserScope,
) -> Mapping[str, Type | int]:
    generic_type_params: Mapping[str, Type | int] = {}
    if context.peek_token().type == TokenType.LCURLY:
        context.advance_token()
        # Generic type
        generic_type_params = _consume_concrete_generic_type_parameters_list(context)
        context.expect_token(TokenType.RCURLY)
        context.advance_token()

    return generic_type_params


def _consume_concrete_generic_type_parameters_list(
    context: ParserScope,
) -> Mapping[str, Type | int]:
    type_params: Mapping[
        str,
        Type | int,
    ] = {}  # TODO(@kirillzhosul): Named type but also can be value argument (param)
    while token := context.peek_token():
        if token.type == TokenType.RCURLY:
            break
        context.expect_token(TokenType.IDENTIFIER)
        typename_token = context.next_token()

        context.expect_token(TokenType.ASSIGNMENT)
        context.advance_token()

        typename = typename_token.text

        if context.peek_token().type == TokenType.INTEGER:
            tok = context.next_token()
            assert isinstance(tok.value, int)
            type_params[typename] = tok.value
        else:
            type_params[typename] = parse_concrete_type_from_tokenizer(
                context,
                allow_inferring_variable_types=False,
            )

        t = context.peek_token()
        if t.type == TokenType.RCURLY:
            break
        context.expect_token(TokenType.COMMA)
        _ = context.next_token()
    return type_params


def consume_generic_type_parameters(context: ParserScope) -> Mapping[str, Token]:
    """Consume parameters for generic type definition if specified (e.g cursor points at `{`.

    e.g X{T, N}
    Otherwise returns empty type parameters.
    """
    generic_type_params: Mapping[str, Token] = {}
    if context.peek_token().type == TokenType.LCURLY:
        context.advance_token()
        # Generic type
        generic_type_params = _consume_generic_type_parameters_list(context)
        context.expect_token(TokenType.RCURLY)
        context.advance_token()

    return generic_type_params


def _consume_generic_type_parameters_list(
    context: ParserScope,
) -> Mapping[str, Token]:
    """Read `consume_generic_type_parameters`."""
    type_params: Mapping[str, Token] = {}
    while token := context.peek_token():
        if token.type == TokenType.RCURLY:
            break
        context.expect_token(TokenType.IDENTIFIER)
        t_token = context.next_token()
        type_params[t_token.text] = t_token
        t = context.peek_token()
        if t.type == TokenType.RCURLY:
            break
        context.expect_token(TokenType.COMMA)
        _ = context.next_token()
    return type_params
