from typing import assert_never

from libgofra.hir.literals import (
    ArrayLiteral,
    BooleanLiteral,
    CharacterLiteral,
    IntegerLiteral,
    Literal_T,
    StringLiteral,
    StructureLiteral,
)
from libgofra.types._base import Type
from libgofra.types.composite.array import ArrayType
from libgofra.types.composite.pointer import PointerMemoryLocation, PointerType
from libgofra.types.composite.string import StringType
from libgofra.types.composite.structure import StructureType
from libgofra.types.primitive.boolean import BoolType
from libgofra.types.primitive.character import CharType
from libgofra.types.primitive.integers import I64Type
from libgofra.types.registry import TypeRegistry


def infer_type_from_literal(literal: Literal_T, types: TypeRegistry) -> Type:
    """Infer a type of given literal from its syntactic form.

    Types are inferred bottom-up: a literal has a type by its own shape, and
    composite literals are inferred from their elements.
    """
    match literal:
        case IntegerLiteral():
            return I64Type()
        case CharacterLiteral():
            return CharType()
        case StringLiteral():
            return PointerType(
                points_to=StringType(),
                memory_location=PointerMemoryLocation.STATIC,
            )
        case BooleanLiteral():
            return BoolType()
        case StructureLiteral(name=name):
            if not name:
                msg = f"Cannot infer type for structure literal with no name {literal.token.location}"
                raise ValueError(msg)
            structure = types.get(name)
            if structure is None:
                msg = "unknown structure "
                raise ValueError(msg)

            if not isinstance(structure, StructureType):
                msg = "not an structure"
                raise ValueError(msg)  # noqa: TRY004

            return structure
        case ArrayLiteral(elements=elements):
            if not elements:
                msg = "Cannot infer type for array literal with no elements"
                raise ValueError(msg)
            element_literal = elements[0]
            return ArrayType(
                element_type=infer_type_from_literal(element_literal, types),
                elements_count=len(elements),
            )
        case _:
            assert_never(literal)
