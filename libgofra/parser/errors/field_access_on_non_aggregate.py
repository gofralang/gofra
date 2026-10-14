from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation
from libgofra.types._base import Type


class FieldAccessOnNonAggregateTypeError(GofraError):
    def __init__(
        self,
        *,
        bound_type: Type,
        at: TokenLocation,
        field: str | None = None,
    ) -> None:
        self.bound_type = bound_type
        self.at = at
        self.field = field

    def __repr__(self) -> str:
        return f"""Cannot access field on non-aggregate type `{self.bound_type}` at {self.at}

help: pointers are auto-dereferenced one level;
      dereference further pointers explicitly

{self.generic_error_name}"""
