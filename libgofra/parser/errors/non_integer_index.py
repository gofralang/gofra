from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation
from libgofra.types import Type


class NonIntegerIndexError(GofraError):
    def __init__(
        self,
        t: Type,
        at: TokenLocation,
    ) -> None:
        self.at = at
        self.t = t

    def __repr__(self) -> str:
        return f"""Index must be an integer at {self.at}

Tried to index with type {self.t}

{self.generic_error_name}"""
