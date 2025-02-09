from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Generator

type TokenValue = int | float | str
type TokenLocation = tuple[str, int, int]
type TokenGenerator = Generator[Token]


class TokenType(IntEnum):
    INTEGER = auto()
    FLOAT = auto()

    SYMBOL = auto()
    STRING = auto()

    WORD = auto()
    KEYWORD = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    text: str
    value: TokenValue
    location: TokenLocation

    def __repr__(self) -> str:
        return f"Token<{self.type.name}, {self.value}>"
