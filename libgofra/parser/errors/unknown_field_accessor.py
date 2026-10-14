from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation
from libgofra.types.composite import UnionType
from libgofra.types.composite.structure import StructureType


class UnknownFieldAccessorError(GofraError):
    def __init__(
        self,
        field: str,
        at: TokenLocation,
        aggregate: StructureType | UnionType,
    ) -> None:
        self.field = field
        self.at = at
        self.aggregate = aggregate

    def __repr__(self) -> str:
        kind = "structure" if isinstance(self.aggregate, StructureType) else "union"
        known = (
            ", ".join(self.aggregate.natural_fields)
            if isinstance(self.aggregate, StructureType)
            else ", ".join(self.aggregate.members)
        )
        return f"""Unknown {kind} field accessor!

Tried to access '{self.field} at {self.at} but it is not a field of {self.aggregate.name}

Type: {self.aggregate}
Known fields: {known}

{self.generic_error_name}"""
