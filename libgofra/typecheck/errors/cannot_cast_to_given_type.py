from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation
from libgofra.types._base import Type


class CannotCastToGivenTypeError(GofraError):
    """Raised when a typecast between two types is not allowed."""

    def __init__(
        self,
        *,
        source: Type,
        target: Type,
        at: TokenLocation,
    ) -> None:
        self.source = source
        self.target = target
        self.at = at

    def __repr__(self) -> str:
        return f"""Cannot cast '{self.source}' to '{self.target}' at {self.at}.

From: {self.source} ({self.source.size_in_bytes} bytes)
To:   {self.target} ({self.target.size_in_bytes} bytes)

Tried to resolve which cast kind to use, but failed to find any safe possible strategy:
(REINTERPRET, TRUNCATE, EXTEND, NORMALIZE_BOOL)

Prohibited to use REINTERPRET cast!

{self.generic_error_name}"""
