from dataclasses import dataclass
from enum import IntEnum, auto
from pathlib import Path

type TokenValue = int | float | str


@dataclass(frozen=True)
class TokenLocation:
    filepath: Path
    line_number: int
    col_number: int

    def __repr__(self) -> str:
        return f"'{self.filepath.name}:{self.line_number + 1}:{self.col_number + 1}'"


class TokenType(IntEnum):
    INTEGER = auto()

    CHARACTER = auto()
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
