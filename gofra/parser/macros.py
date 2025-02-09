from dataclasses import dataclass

from gofra.lexer import Token
from gofra.lexer.tokens import TokenLocation


@dataclass(frozen=True)
class Macro:
    location: TokenLocation
    expanded_tokens: list[Token]
