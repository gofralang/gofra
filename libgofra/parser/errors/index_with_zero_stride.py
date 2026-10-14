from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation
from libgofra.types import Type


class IndexWithZeroStrideError(GofraError):
    def __init__(self, t: Type, underlying_type: Type, at: TokenLocation) -> None:
        self.t = t
        self.underlying_type = underlying_type
        self.at = at

    def __repr__(self) -> str:
        return f"""Index with zero stride at {self.at}!

Tried to index type `{self.t}` which resolves to underlying type `{self.underlying_type}` (which has size {self.underlying_type.size_in_bytes})

It is impossible to index such type!

{self.generic_error_name}"""
