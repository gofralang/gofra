from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation
from libgofra.types import ArrayType, PointerType, Type


class NotIndexableError(GofraError):
    def __init__(self, type_: Type, at: TokenLocation) -> None:
        self.type = type_
        self.at = at

    def __repr__(self) -> str:
        return f"""Cannot apply index `[..]` to type '{self.type}' at {self.at}.

Only arrays and pointers allows indexing!

Consider wrapping in a pointer ({PointerType(self.type)}) or using an array ({ArrayType(self.type, 0)}).

{self.generic_error_name}"""
