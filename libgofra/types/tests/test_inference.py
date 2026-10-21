# libgofra/types/tests/test_inference.py

import pytest

from libgofra.hir.literals import (
    ArrayLiteral,
    BooleanLiteral,
    CharacterLiteral,
    IntegerLiteral,
    StringLiteral,
    StructureLiteral,
)
from libgofra.lexer.tokens import Token, TokenLocation, TokenType
from libgofra.types.composite.array import ArrayType
from libgofra.types.composite.pointer import PointerMemoryLocation, PointerType
from libgofra.types.composite.string import StringType
from libgofra.types.composite.structure import StructureType
from libgofra.types.inference import infer_type_from_literal
from libgofra.types.primitive.boolean import BoolType
from libgofra.types.primitive.character import CharType
from libgofra.types.primitive.integers import I64Type
from libgofra.types.registry import TypeRegistry


def _token() -> Token:
    return Token(
        type=TokenType.INTEGER,
        text="0",
        value=0,
        location=TokenLocation.toolchain(),
    )


def _registry() -> TypeRegistry:
    return TypeRegistry(
        {
            "int": I64Type(),
            "Point": StructureType(
                name="Point",
                fields={"x": I64Type(), "y": I64Type()},
                order=["x", "y"],
                is_packed=False,
            ),
        },
    )


# --- primitives ---


def test_infers_integer_literal() -> None:
    t = infer_type_from_literal(IntegerLiteral(token=_token(), value=42), _registry())

    assert isinstance(t, I64Type)


def test_infers_character_literal() -> None:
    t = infer_type_from_literal(CharacterLiteral(token=_token(), value=65), _registry())

    assert isinstance(t, CharType)


def test_infers_boolean_literal() -> None:
    t = infer_type_from_literal(BooleanLiteral(token=_token(), value=True), _registry())

    assert isinstance(t, BoolType)


def test_infers_string_literal_as_static_pointer() -> None:
    t = infer_type_from_literal(StringLiteral(token=_token(), value="hi"), _registry())

    assert isinstance(t, PointerType)
    assert isinstance(t.points_to, StringType)
    assert t.memory_location == PointerMemoryLocation.STATIC


# --- composites ---


def test_infers_structure_literal_by_name() -> None:
    literal = StructureLiteral(token=_token(), name="Point", fields={})

    t = infer_type_from_literal(literal, _registry())

    assert isinstance(t, StructureType)
    assert t.name == "Point"


def test_infers_array_literal_from_first_element() -> None:
    literal = ArrayLiteral(
        token=_token(),
        elements=[IntegerLiteral(token=_token(), value=1)],
        default=None,
    )

    t = infer_type_from_literal(literal, _registry())

    assert isinstance(t, ArrayType)
    assert isinstance(t.element_type, I64Type)
    assert t.elements_count == 1


def test_infers_nested_array_literal() -> None:
    literal = ArrayLiteral(
        token=_token(),
        elements=[
            ArrayLiteral(
                token=_token(),
                elements=[IntegerLiteral(token=_token(), value=1)],
                default=None,
            ),
        ],
        default=None,
    )

    t = infer_type_from_literal(literal, _registry())

    assert isinstance(t, ArrayType)
    assert isinstance(t.element_type, ArrayType)
    assert isinstance(t.element_type.element_type, I64Type)


# --- errors ---


def test_fails_on_structure_literal_without_name() -> None:
    literal = StructureLiteral(token=_token(), name=None, fields={})

    with pytest.raises(ValueError, match="no name"):
        infer_type_from_literal(literal, _registry())


def test_fails_on_unknown_structure() -> None:
    literal = StructureLiteral(token=_token(), name="Unknown", fields={})

    with pytest.raises(ValueError, match="unknown structure"):
        infer_type_from_literal(literal, _registry())


def test_fails_on_non_structure_type() -> None:
    literal = StructureLiteral(token=_token(), name="int", fields={})

    with pytest.raises(ValueError, match="not an structure"):
        infer_type_from_literal(literal, _registry())


def test_fails_on_empty_array_literal() -> None:
    literal = ArrayLiteral(token=_token(), elements=[], default=None)

    with pytest.raises(ValueError, match="no elements"):
        infer_type_from_literal(literal, _registry())
