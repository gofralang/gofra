from dataclasses import dataclass
from typing import assert_never

from libgofra.hir.literals import IntegerLiteral
from libgofra.hir.operator import OperatorType
from libgofra.hir.variable import (
    Variable,
)
from libgofra.lexer.tokens import Token, TokenLocation, TokenType
from libgofra.parser._context import ParserContext
from libgofra.parser.errors.field_access_on_non_aggregate import (
    FieldAccessOnNonAggregateTypeError,
)
from libgofra.parser.errors.index_out_of_bounds import IndexOutOfBoundError
from libgofra.parser.errors.index_with_zero_stride import IndexWithZeroStrideError
from libgofra.parser.errors.non_integer_index import NonIntegerIndexError
from libgofra.parser.errors.type_is_not_indexable import NotIndexableError
from libgofra.parser.errors.unknown_field_accessor import (
    UnknownFieldAccessorError,
)
from libgofra.parser.runtime_oob_check import emit_runtime_hir_oob_check
from libgofra.types._base import Type
from libgofra.types.composite.array import ArrayType
from libgofra.types.composite.pointer import PointerType
from libgofra.types.composite.slice import SliceType
from libgofra.types.composite.structure import StructureType
from libgofra.types.composite.union import UnionType
from libgofra.types.primitive.character import CharType
from libgofra.types.primitive.integers import IntegerType


@dataclass
class FieldAccessor:
    field: str


@dataclass
class IndexAccessor:
    index: int | Variable[Type]


@dataclass
class _VariableAccessorExpr:
    variable: Variable[Type]
    is_reference: bool

    chain: list[FieldAccessor | IndexAccessor]

    def is_direct_expr(self) -> bool:
        return not self.is_reference and not self.chain


def _resolve_indexable_type(t: Type, token: Token) -> tuple[Type, int, int | None]:
    """Transform indexable type T to underlying type after indexation via offsetting such type by stride.

    Where indexable types is:
        - Arrays, Pointer

    Auto-dereference pointers to arrays such that stride is element size

    :returns: Underlying type, stride, elements count (OOB)
    """
    if isinstance(t, PointerType):
        inner = t.points_to
        if isinstance(inner, ArrayType):
            # *T[N] -> element T, stride sizeof(T)
            return (
                inner.element_type,
                inner.element_type.size_in_bytes,
                inner.elements_count,
            )
        if isinstance(inner, SliceType):
            # *T[N] -> T, stride sizeof(T)
            return (
                inner.element_type,
                inner.element_type.size_in_bytes,
                None,
            )
        # *T -> element T, stride sizeof(T), unsafe OOB
        return inner, inner.size_in_bytes, None
    if isinstance(t, ArrayType):
        # T[N] -> T, stride sizeof(T)
        return (
            t.element_type,
            t.element_type.size_in_bytes,
            t.elements_count,
        )
    if isinstance(t, SliceType):
        # []T -> T, stride sizeof(T)
        return (
            t.element_type,
            t.element_type.size_in_bytes,
            None,
        )

    raise NotIndexableError(t, at=token.location)


def _check_compile_time_oob(
    elements_count: int | None,
    index: int,
    at: TokenLocation,
) -> None:
    if (
        elements_count is not None
        and elements_count != 0  # TODO: Also check for unfinished, remove them
        and isinstance(index, int)
        and (index >= elements_count or index < 0)
    ):
        raise IndexOutOfBoundError(
            index=index,
            bound=elements_count,
            at=at,
        )


def _lower_index_accessor_expr(
    context: ParserContext,
    bound_type: Type,
    accessor: IndexAccessor,
    token: Token,
) -> Type:
    resolved_type, stride, elements_count = _resolve_indexable_type(bound_type, token)

    if stride == 0:
        raise IndexWithZeroStrideError(bound_type, resolved_type, at=token.location)

    if isinstance(bound_type, PointerType):
        # Dereference *T, such we will work against target type, not holder
        context.push_new_operator(
            type=OperatorType.MEMORY_VARIABLE_READ,
            token=token,
        )
        bound_type = bound_type.points_to

    if isinstance(bound_type, SliceType):
        context.push_new_operator(
            type=OperatorType.STRUCT_FIELD_OFFSET,
            token=token,
            operand=(bound_type, "data"),
        )
        context.push_new_operator(
            type=OperatorType.MEMORY_VARIABLE_READ,
            token=token,
        )

    if isinstance(accessor.index, int):
        # Access constant by integer (direct int or expanded from constant)

        # TODO(perf): optimize and not push these operators if zero-offset
        _check_compile_time_oob(elements_count, accessor.index, token.location)
        context.push_new_operator(
            type=OperatorType.PUSH_INTEGER,
            token=token,
            operand=stride * accessor.index,
        )
        context.push_new_operator(
            type=OperatorType.ARITHMETIC_PLUS,
            token=token,
        )
        return resolved_type

    assert isinstance(accessor.index, Variable)
    if not isinstance(accessor.index.type, (IntegerType, CharType)):
        raise NonIntegerIndexError(accessor.index.type, at=token.location)

    if accessor.index.is_constant and isinstance(accessor.index.initial_value, int):
        # Fold constant into direct accessor
        accessor.index = accessor.index.initial_value
        return _lower_index_accessor_expr(
            context,
            bound_type,
            accessor,
            token,
        )

    # Access by non-constant variable
    context.push_new_operator(
        OperatorType.PUSH_INTEGER,
        token,
        operand=stride,
    )
    context.push_new_operator(
        OperatorType.PUSH_VARIABLE_VALUE,
        token,
        operand=accessor.index.name,
    )
    if context.rt_array_oob_check:
        assert elements_count
        emit_runtime_hir_oob_check(
            context,
            token,
            accessor.index,
            elements_count,
        )
    context.push_new_operator(OperatorType.ARITHMETIC_MULTIPLY, token)
    context.push_new_operator(OperatorType.ARITHMETIC_PLUS, token)
    return resolved_type


def _lower_try_derefence_to_aggregate_type(
    context: ParserContext,
    t: Type,
    token: Token,
) -> Type:
    """Dereference to aggregate type from pointer to it, or skip if already got any aggregate type, suitable for field accessors."""
    if isinstance(t, PointerType):
        if not isinstance(t.points_to, (StructureType, UnionType)):
            raise FieldAccessOnNonAggregateTypeError(
                bound_type=t,
                at=token.location,
            )

        # If we have struct field accessor for analogue of `->` (E.g *struct)
        # we must dereference that struct pointer and deal with direct pointer to it
        # struct is remapped to pointer holding that type
        # (-auto-deref-)
        context.push_new_operator(
            type=OperatorType.MEMORY_VARIABLE_READ,
            token=token,
        )
        return t.points_to

    if isinstance(t, (StructureType, UnionType)):
        return t

    raise FieldAccessOnNonAggregateTypeError(
        bound_type=t,
        at=token.location,
    )


def _lower_field_accessor_expr(
    context: ParserContext,
    bound_type: Type,
    accessor: FieldAccessor,
    token: Token,
) -> Type:
    bound_type = _lower_try_derefence_to_aggregate_type(context, bound_type, token)

    assert isinstance(bound_type, (StructureType, UnionType))
    if isinstance(bound_type, StructureType):
        if not bound_type.has_field(accessor.field):
            raise UnknownFieldAccessorError(
                accessor.field,
                token.location,
                bound_type,
            )

        context.push_new_operator(
            type=OperatorType.STRUCT_FIELD_OFFSET,
            token=token,
            operand=(bound_type, accessor.field),
        )
        return bound_type.get_field_type(accessor.field)
    if isinstance(bound_type, UnionType):
        if not bound_type.has_member(accessor.field):
            raise UnknownFieldAccessorError(
                accessor.field,
                token.location,
                bound_type,
            )

        # As it is union any field is same as field itself, so we just typecast for typechecker to know that we are dereference/lowered it
        bound_type = bound_type.get_member_type(accessor.field)
        context.push_new_operator(
            OperatorType.STATIC_TYPE_CAST,
            token,
            operand=PointerType(bound_type),
        )
        return bound_type
    assert_never(bound_type)


def _lower_expr_into_offset_reference(
    context: ParserContext,
    token: Token,
    expr: _VariableAccessorExpr,
) -> Type:
    if expr.is_direct_expr():
        # var x; x;
        context.push_new_operator(
            type=OperatorType.PUSH_VARIABLE_VALUE,
            token=token,
            operand=expr.variable.name,
        )
        return expr.variable.type

    context.push_new_operator(
        type=OperatorType.PUSH_VARIABLE_ADDRESS,
        token=token,
        operand=expr.variable.name,
    )

    bound_type = expr.variable.type  # Assume PointerType under the hood

    for accessor in expr.chain:
        match accessor:
            case IndexAccessor():
                bound_type = _lower_index_accessor_expr(
                    context,
                    bound_type,
                    accessor,
                    token,
                )
            case FieldAccessor():
                bound_type = _lower_field_accessor_expr(
                    context,
                    bound_type,
                    accessor,
                    token,
                )
    if not expr.is_reference:
        context.push_new_operator(
            type=OperatorType.MEMORY_VARIABLE_READ,
            token=token,
        )
        return bound_type

    return PointerType(bound_type)


def try_parse_variable_accessor_expr(context: ParserContext, token: Token) -> bool:
    if not (expr := _try_parse_variable_accesor_expr_spec(context, token)):
        return False

    if _try_unwind_constant(context, token, expr):
        return True

    variable = expr.variable
    if expr.is_reference and variable.is_constant:
        # Probably we must allow reference but mark them as immutable memory locations
        # this was easiest solution at that time
        msg = f"Tried to get reference of constant variable {variable.name} at {token.location}"
        raise ValueError(msg)

    bound_type = _lower_expr_into_offset_reference(context, token, expr)
    if bound_type.size_in_bytes > 8:
        msg = f"Cannot load expression result onto stack as it has type {bound_type} which size is {bound_type.size_in_bytes} in bytes (stack-cell-overflow) at {token.location}"
        raise ValueError(msg)

    return True


def _try_unwind_constant(
    context: ParserContext,
    token: Token,
    expr: _VariableAccessorExpr,
) -> bool:

    if not expr.variable.is_constant:
        return False

    if not expr.is_direct_expr():
        return False  # Chain, cant unwind

    assert expr.variable.initial_value is not None, (
        expr.variable.defined_at,
        token.location,
    )

    if isinstance(expr.variable.initial_value, IntegerLiteral):
        context.push_new_operator(
            type=OperatorType.PUSH_INTEGER,
            token=token,
            operand=expr.variable.initial_value.value,
        )

        assert expr.variable.size_in_bytes == 8
        return True

    return False


def _try_parse_variable_accesor_expr_spec(
    context: ParserContext,
    token: Token,
) -> _VariableAccessorExpr | None:
    assert token.type == TokenType.IDENTIFIER
    varname = token.text

    is_reference = False
    if varname.startswith("&"):
        is_reference = True
        varname = varname.removeprefix("&")

    variable = context.scope.lookup(varname)
    if variable is None or not isinstance(variable, Variable):
        return None

    expr = _VariableAccessorExpr(
        variable=variable,
        is_reference=is_reference,
        chain=[],
    )

    # There, we have an finite referenced object
    # e.g `a.x` and we are after `a`

    while True:
        accessor_token = context.peek_token()

        if accessor_token.type == TokenType.LBRACKET:
            context.advance_token()  # Consume LBRACKET

            elements_token = context.next_token()
            if elements_token.type not in (TokenType.INTEGER, TokenType.IDENTIFIER):
                msg = f"Expected index inside of [], but got {elements_token.type.name}"
                raise ValueError(msg)

            rbracket = context.next_token()
            if rbracket.type != TokenType.RBRACKET:
                msg = f"Expected RBRACKET after index accessor but got {rbracket.type.name} at {token.location}"
                raise ValueError(msg)

            if elements_token.type == TokenType.INTEGER:
                # Simple integer array access
                assert isinstance(elements_token.value, int)
                expr.chain.append(IndexAccessor(elements_token.value))
                continue

            # Variable index access
            assert elements_token.type == TokenType.IDENTIFIER
            assert isinstance(elements_token.value, str)
            index_var = context.scope.lookup(elements_token.value)
            if index_var is None or not isinstance(index_var, Variable):
                msg = f"Expected known variable at {token.location} as index but got unknown variable '{elements_token.value}'"
                raise ValueError(msg)

            expr.chain.append(IndexAccessor(index_var))
            continue

        if (
            accessor_token.type == TokenType.DOT
            and not accessor_token.has_trailing_whitespace  # No space after dot
        ):
            context.advance_token()  # Consume DOT
            field_token = context.next_token()
            if field_token.type != TokenType.IDENTIFIER:
                msg = f"Expected struct field accessor to be an identifier, but got {field_token.type.name}"
                raise ValueError(msg)
            expr.chain.append(FieldAccessor(field_token.text))
            continue
        break
    return expr
