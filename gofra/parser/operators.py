from dataclasses import dataclass
from enum import IntEnum, auto

from gofra.lexer import Token

from .intrinsics import Intrinsic

type OperatorOperand = int | float | str | None | Intrinsic


class OperatorType(IntEnum):
    PUSH_INTEGER = auto()
    PUSH_FLOAT = auto()

    PUSH_SYMBOL = auto()
    PUSH_STRING = auto()

    INTRINSIC = auto()

    IF = auto()
    WHILE = auto()
    DO = auto()
    ELSE = auto()
    END = auto()


@dataclass(frozen=False)
class Operator:
    type: OperatorType
    token: Token
    operand: OperatorOperand

    def __repr__(self) -> str:
        return f"Operator<{self.type.name}, {self.token}, operand={self.operand}>"
