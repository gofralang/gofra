from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from libgofra.lexer import Token

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass
class BaseLiteral:
    token: Token = field(repr=False)


@dataclass
class IntegerLiteral(BaseLiteral):
    value: int


@dataclass
class CharacterLiteral(BaseLiteral):
    value: int


@dataclass
class BooleanLiteral(BaseLiteral):
    value: bool


@dataclass
class StructureLiteral(BaseLiteral):
    name: str | None
    fields: "Mapping[str, Literal_T]"


@dataclass
class ArrayLiteral(BaseLiteral):
    elements: list["Literal_T"]
    default: "Literal_T | None"


@dataclass
class StringLiteral(BaseLiteral):
    value: str


type Literal_T = (
    IntegerLiteral
    | CharacterLiteral
    | BooleanLiteral
    | StructureLiteral
    | ArrayLiteral
    | StringLiteral
)
