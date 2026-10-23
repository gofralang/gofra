from libgofra.types._base import Type
from libgofra.types.primitive.integers import IntegerType


class EnumType(IntegerType):
    """Primitive enum type backed by its underlying primitive type."""

    name: str
    underlying_type: Type
    variants: dict[str, int]

    def __init__(
        self,
        name: str,
        underlying_type: Type,
        variants: dict[str, int],
    ) -> None:
        self.name = name
        self.underlying_type = underlying_type
        self.variants = variants

        self.size_in_bytes = underlying_type.size_in_bytes
        self.alignment = underlying_type.alignment
        self.is_fp = False

    def __repr__(self) -> str:
        return f"Enum {self.name}"
