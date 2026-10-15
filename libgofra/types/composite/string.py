from libgofra.types.composite.pointer import PointerMemoryLocation
from libgofra.types.composite.slice import SliceType
from libgofra.types.primitive.character import CharType


class StringType(SliceType):
    """Type that holds string as an slice of CString."""

    def __init__(self) -> None:
        super().__init__(
            element_type=CharType(),
            pma=PointerMemoryLocation.STATIC_READONLY,
        )
        self.name = "string"

    def __repr__(self) -> str:
        return self.name
