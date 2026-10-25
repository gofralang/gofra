from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from libgofra.codegen.float_bits import float_to_bits
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
from libgofra.types import ArrayType, BoolType, CharType, PointerType, Type
from libgofra.types.composite import StringType, StructureType
from libgofra.types.primitive.floats import F64Type
from libgofra.types.primitive.integers import I64Type, IntegerType


@dataclass(frozen=True, slots=True)
class VariableIntArrayInitializerValue:
    """HIR value parsed from initializer for int array.

    Variable must be initialized with this value.
    """

    default: int
    values: list[int]


@dataclass(frozen=True, slots=True)
class VariableIntSliceInitializerValue:
    data_initializer: VariableIntArrayInitializerValue


@dataclass(frozen=True, slots=True)
class VariableStringPtrArrayInitializerValue:
    """HIR value parsed from initializer for *string array.

    Variable must be initialized with this value.
    """

    default: int
    values: list[str]


@dataclass(frozen=True, slots=True)
class VariableIntFieldedStructureInitializerValue:
    """HIR value parsed from initializer for structure where all fields are integers and fulfilled."""

    values: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class VariableStringPtrInitializerValue:
    """HIR value parsed from initializer for string (e.g *string / string).

    Variable must be initialized with this value.
    """

    string: str


type T_AnyVariableInitializer = (
    int
    | VariableIntArrayInitializerValue
    | VariableStringPtrInitializerValue
    | VariableStringPtrArrayInitializerValue
    | VariableIntFieldedStructureInitializerValue
    | VariableIntSliceInitializerValue
)


_ = VariableIntSliceInitializerValue


def literal_to_codegen_initializer(  # noqa: PLR0911
    literal: Literal_T,
    target_type: Type,
) -> T_AnyVariableInitializer:
    match (literal, target_type):
        case (
            IntegerLiteral(value=v) | CharacterLiteral(value=v),
            IntegerType() | CharType() | BoolType(),
        ):
            return v
        case (BooleanLiteral(value=v), BoolType()):
            return int(v)
        case (FloatLiteral(value=v), F64Type()):
                        return float_to_bits(v)
        case (StringLiteral(value=s), PointerType(points_to=StringType())):
            return VariableStringPtrInitializerValue(string=s)

        case ArrayLiteral(elements=elems, default=filler), ArrayType():
            flat_el_t = target_type.flatten().element_type
            match flat_el_t:
                case I64Type() | F64Type():
                    element_t = I64Type() if isinstance(flat_el_t, I64Type) else F64Type()
                    int_values = [
                        literal_to_codegen_initializer(e, element_t) for e in elems
                    ]
                    if not all(isinstance(v, int) for v in int_values):
                        msg = "Non-int array literal not supported by codegen"
                        raise NotImplementedError(msg)
                    int_values = cast("list[int]", int_values)
                    default = (
                        literal_to_codegen_initializer(filler, element_t)
                        if filler
                        else 0
                    )
                    if not isinstance(default, int):
                        msg_0 = "Non-int filler not supported"
                        raise NotImplementedError(msg_0)
                    return VariableIntArrayInitializerValue(
                        default=default,
                        values=int_values,
                    )
                case PointerType(points_to=StringType()):
                    str_values = [
                        literal_to_codegen_initializer(
                            e,
                            PointerType(points_to=StringType()),
                        )
                        for e in elems
                    ]
                    if not all(
                        isinstance(v, VariableStringPtrInitializerValue)
                        for v in str_values
                    ):
                        raise NotImplementedError
                    str_values = cast(
                        "list[VariableStringPtrInitializerValue]",
                        str_values,
                    )
                    assert not filler
                    return VariableStringPtrArrayInitializerValue(
                        default=0,
                        values=[v.string for v in str_values],
                    )
                case _:
                    raise NotImplementedError(literal)

        case (StructureLiteral(fields=fields), StructureType()):
            int_fields = {}
            for field_name, field_lit in fields.items():
                if not isinstance(field_lit, IntegerLiteral):
                    msg = "Non-int struct field not supported by codegen"
                    raise NotImplementedError(msg)
                int_fields[field_name] = field_lit.value
            return VariableIntFieldedStructureInitializerValue(values=int_fields)
        case _:
            raise NotImplementedError(literal)
