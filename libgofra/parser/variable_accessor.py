from dataclasses import dataclass
from typing import cast

from libgofra.exceptions import GofraError
from libgofra.hir.operator import OperatorType
from libgofra.hir.variable import (
    Variable,
)
from libgofra.lexer.tokens import Token, TokenType
from libgofra.parser._context import ParserScope
from libgofra.parser.errors.static_array_out_of_bounds import ArrayOutOfBoundsError
from libgofra.parser.errors.unknown_field_accessor_struct_field import (
    UnknownFieldAccessorStructFieldError,
)
from libgofra.parser.runtime_oob_check import emit_runtime_hir_oob_check
from libgofra.types._base import Type
from libgofra.types.composite.array import ArrayType
from libgofra.types.composite.pointer import PointerType
from libgofra.types.composite.structure import StructureType
from libgofra.types.composite.union import UnionType
from libgofra.types.primitive.character import CharType
from libgofra.types.primitive.integers import I64Type


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


def _lower_expr_into_offset_reference(
    context: ParserScope,
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
                if not isinstance(bound_type, ArrayType) and (
                    not isinstance(bound_type, PointerType)
                    or not isinstance(bound_type.points_to, ArrayType)
                ):
                    msg = f"cannot get index-of (e.g []) for non-array types (nor pointers to arrays). at {token.location}"
                    raise TypeError(msg)

                if isinstance(bound_type, PointerType):
                    # (-auto-deref-)
                    assert isinstance(bound_type.points_to, ArrayType)
                    context.push_new_operator(
                        type=OperatorType.MEMORY_VARIABLE_READ,
                        token=token,
                    )
                    bound_type = bound_type.points_to
                if isinstance(accessor.index, int):
                    # Access by integer (direct int or expanded from constant)
                    # Compile-time OOB checks
                    if bound_type.elements_count and bound_type.is_index_oob(
                        accessor.index,
                    ):  # TODO: treat as an warning (unfinished array)
                        raise ArrayOutOfBoundsError(
                            at=token.location,
                            # TODO: Error notes variable while may reference bound type in chain
                            variable=cast("Variable[ArrayType]", expr.variable),
                            array_index_at=accessor.index,
                        )

                    shift_in_bytes = bound_type.get_index_offset(accessor.index)
                    if shift_in_bytes or True:  # noqa: SIM222
                        # TODO(@kirillzhosul): remove after typechecker refactor
                        context.push_new_operator(
                            type=OperatorType.PUSH_INTEGER,
                            token=token,
                            operand=shift_in_bytes,
                        )
                        context.push_new_operator(
                            type=OperatorType.ARITHMETIC_PLUS,
                            token=token,
                        )
                    bound_type = bound_type.element_type  # lowering
                    continue

                assert isinstance(accessor.index, Variable)
                var = accessor.index
                if not isinstance(var.type, (I64Type, CharType)):
                    msg = f"Non I64/char type cannot be used as index at {token.location}!"
                    raise TypeError(msg)
                if var.is_constant and isinstance(var.initial_value, int):
                    # Unwind constant ref into accessor
                    accessor.index = var.initial_value

                # Access by non-constant variable
                context.push_new_operator(
                    OperatorType.PUSH_INTEGER,
                    token,
                    operand=bound_type.element_type.size_in_bytes,
                )
                context.push_new_operator(
                    OperatorType.PUSH_VARIABLE_VALUE,
                    token,
                    operand=var.name,
                )
                if context.rt_array_oob_check:
                    assert isinstance(var.type, (I64Type, CharType))
                    array_index_at = cast("Variable[I64Type]", accessor.index)
                    emit_runtime_hir_oob_check(
                        context,
                        token,
                        array_index_at,
                        bound_type.elements_count,
                    )
                context.push_new_operator(OperatorType.ARITHMETIC_MULTIPLY, token)
                context.push_new_operator(OperatorType.ARITHMETIC_PLUS, token)
                bound_type = bound_type.element_type  # lowering
                continue
            case FieldAccessor():
                # TODO: check field accessor on pointer to non structs
                if (
                    not isinstance(bound_type, StructureType)
                    and not isinstance(
                        bound_type,
                        PointerType,
                    )
                    and not isinstance(bound_type, UnionType)
                ):
                    msg = f"cannot use field accessor for non-structure/union or pointers to structure types at {token.location}."
                    raise TypeError(msg)

                if isinstance(bound_type, PointerType):
                    if isinstance(
                        bound_type.points_to,
                        StructureType,
                    ):
                        # If we have struct field accessor for analogue of `->` (E.g *struct)
                        # we must dereference that struct pointer and deal with direct pointer to it
                        # struct is remapped to pointer holding that type
                        # (-auto-deref-)
                        context.push_new_operator(
                            type=OperatorType.MEMORY_VARIABLE_READ,
                            token=token,
                        )
                        bound_type = bound_type.points_to
                    else:
                        msg = f"cannot use field accessor for pointers to non structures at {token.location}."
                        raise TypeError(msg)
                if isinstance(bound_type, StructureType):
                    field = accessor.field
                    if not bound_type.has_field(field):
                        raise UnknownFieldAccessorStructFieldError(
                            field,
                            token.location,
                            bound_type,
                        )

                    context.push_new_operator(
                        type=OperatorType.STRUCT_FIELD_OFFSET,
                        token=token,
                        operand=(bound_type, field),
                    )
                    bound_type = bound_type.get_field_type(field)  # lowering
                    continue
                assert isinstance(bound_type, UnionType)
                member = accessor.field
                if not bound_type.has_member(member):
                    msg = f"no member at {token.location}"
                    raise GofraError(msg)

                # were just lowering hier sir
                bound_type = bound_type.get_member_type(member)  # lowering
                context.push_new_operator(
                    OperatorType.STATIC_TYPE_CAST,
                    token,
                    operand=PointerType(bound_type),
                )
                continue
    if not expr.is_reference:
        context.push_new_operator(
            type=OperatorType.MEMORY_VARIABLE_READ,
            token=token,
        )
        return bound_type

    return PointerType(bound_type)


def try_push_variable_reference(context: ParserScope, token: Token) -> bool:
    if not (expr := _resolve_variable_expr(context, token)):
        return False

    if _try_unwind_constant(context, token, expr):
        return True

    variable = expr.variable
    if expr.is_reference and variable.is_constant:
        # Probably we must allow reference but mark them as immutable memory locations
        # this was easiest solution at that time
        msg = f"Tried to get reference of constant variable {variable.name} at {token.location}"
        raise ValueError(msg)

    _lower_expr_into_offset_reference(context, token, expr)
    if not expr.is_reference and variable.type.size_in_bytes > 8 and not expr.chain:
        # TODO: Check after expr?
        msg = f"Cannot load variable {variable.name} of type {variable.type} as it has size {variable.type.size_in_bytes} in bytes (stack-cell-overflow) at {token.location}"
        raise ValueError(msg)

    return True


def _try_unwind_constant(
    context: ParserScope,
    token: Token,
    expr: _VariableAccessorExpr,
) -> bool:
    if (
        expr.variable.is_constant
        and expr.variable.type.size_in_bytes <= 8
        and expr.is_direct_expr()
        and expr.variable.is_primitive_type
    ):
        # Simple unwrapping for constants
        assert isinstance(expr.variable.initial_value, int)
        context.push_new_operator(
            type=OperatorType.PUSH_INTEGER,
            token=token,
            operand=expr.variable.initial_value,
        )
        return True
    return False


def _resolve_variable_expr(
    context: ParserScope,
    token: Token,
) -> _VariableAccessorExpr | None:
    assert token.type == TokenType.IDENTIFIER
    varname = token.text

    is_reference = False
    if varname.startswith("&"):
        is_reference = True
        varname = varname.removeprefix("&")

    variable = context.search_variable_in_context_parents(varname)
    if not variable:
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
            _ = context.next_token()  # Consume LBRACKET

            elements_token = context.next_token()
            if elements_token.type not in (TokenType.INTEGER, TokenType.IDENTIFIER):
                msg = f"Expected (array) index inside of [], but got {elements_token.type.name}"
                raise ValueError(msg)

            rbracket = context.next_token()
            if rbracket.type != TokenType.RBRACKET:
                msg = f"Expected RBRACKET after (array) index element accessor but got {rbracket.type.name} at {token.location}"
                raise ValueError(msg)

            if elements_token.type == TokenType.INTEGER:
                # Simple integer array access
                assert isinstance(elements_token.value, int)
                expr.chain.append(IndexAccessor(elements_token.value))
                continue

            # Variable index access
            assert elements_token.type == TokenType.IDENTIFIER
            assert isinstance(elements_token.value, str)
            index_var = context.search_variable_in_context_parents(
                elements_token.value,
            )
            if index_var is None:
                msg = f"Expected known VARIABLE at {token.location} as array-index-of but unknown variable '{elements_token.value}'"
                raise ValueError(msg)

            expr.chain.append(IndexAccessor(index_var))
            continue

        if (
            accessor_token.type == TokenType.DOT
            and not accessor_token.has_trailing_whitespace  # why there is this?
        ):
            _ = context.next_token()  # Consume DOT
            field_token = context.next_token()
            if field_token.type != TokenType.IDENTIFIER:
                msg = f"Expected struct field accessor to be an identifier, but got {field_token.type.name}"
                raise ValueError(msg)
            expr.chain.append(FieldAccessor(field_token.text))
            continue
        break
    return expr
