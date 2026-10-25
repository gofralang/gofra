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
from libgofra.hir.module import Module
from libgofra.hir.variable import Variable
from libgofra.types import ArrayType, BoolType, CharType, PointerType, Type
from libgofra.types.composite.string import StringType
from libgofra.types.composite.structure import StructureType
from libgofra.types.primitive.floats import F32Type, F64Type
from libgofra.types.primitive.integers import IntegerType


def validate_literal_initializer_against_type(
    literal: Literal_T,
    type: Type,  # noqa: A002
    module: Module,
) -> None:
    match (literal, type):
        case (IntegerLiteral(), IntegerType() | CharType() | BoolType()):
            validate_numeric_literal_fits_type(type, literal)
        case (FloatLiteral(), F64Type()):
            pass
        case (FloatLiteral(), F32Type()):
            pass
        case (CharacterLiteral(), IntegerType() | CharType()):
            validate_numeric_literal_fits_type(type, literal)
        case (BooleanLiteral(), BoolType()):
            pass
        case (StructureLiteral(token=token, fields=fields, name=name), StructureType()):
            abnormals_fields = set(fields.keys()).difference(type.natural_fields)
            if abnormals_fields:
                msg = f"Abnormal field(s) for structure initializer: {abnormals_fields} at {token.location}"
                raise ValueError(msg)

            if name is not None and name != type.name:
                msg = f"{token.location}: expected matching structure name, either drop name or suply correct one"
                raise ValueError(msg)
            missing_fields = set(type.natural_fields).difference(fields.keys())
            if missing_fields:
                msg = f"Missing field(s) for structure initializer: {missing_fields} at {token.location}"
                raise ValueError(msg)

            for field_name, field_literal in fields.items():
                field_type = type.get_field_type(field_name)
                validate_literal_initializer_against_type(
                    field_literal,
                    field_type,
                    module,
                )
        case (
            ArrayLiteral(token=token, elements=elements, default=default),
            ArrayType(),
        ):
            flat = type.flatten()

            if len(elements) > flat.elements_count:
                msg = f"Array initializer got {len(elements)} elements at {token.location}, but array size is {flat} (flattened from {type}) which overflows array!"
                raise ValueError(msg)

            for element in elements:
                validate_literal_initializer_against_type(
                    element,
                    flat.element_type,
                    module,
                )

            if default:
                validate_literal_initializer_against_type(
                    default,
                    flat.element_type,
                    module,
                )

        case (StringLiteral(), PointerType(points_to=StringType())):
            pass
        case _:
            msg = f"Initializer type mismatch: expected {type} but got literal {literal} {literal.token.location}"
            raise NotImplementedError(msg)


def validate_variable_initializer(variable: Variable[Type], module: Module) -> None:
    if variable.initial_value is None:
        return  # No initializer

    validate_literal_initializer_against_type(
        variable.initial_value,
        variable.type,
        module,
    )


def validate_numeric_literal_fits_type(
    t: Type,
    literal: CharacterLiteral | IntegerLiteral,
) -> None:
    bits = t.size_in_bytes * 8
    lo, hi = -(2 ** (bits - 1)), 2 ** (bits - 1) - 1
    if lo <= literal.value <= hi:
        return

    msg = f"Value {literal.value} does not fits type {t} ({lo}..{hi}) at {literal.token.location}"
    raise ValueError(msg)
