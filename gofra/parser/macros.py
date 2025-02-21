from dataclasses import dataclass

from gofra.lexer import Token
from gofra.lexer.tokens import TokenLocation


@dataclass(frozen=True)
class Macro:
    location: TokenLocation
    name: str

    inner_tokens: list[Token]

    def push_token(self, token: Token) -> Token:
        self.inner_tokens.append(token)
        return token
