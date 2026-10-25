from libgofra.types._base import PrimitiveType


class F64Type(PrimitiveType):
    """Float of size 64 bits."""

    size_in_bytes = 8
    alignment = size_in_bytes

    is_fp = True

    def __repr__(self) -> str:
        return "F64"


type AnyFloatType = F32Type | F64Type


class F32Type(PrimitiveType):
    """Float of size 32 bits (IEEE-754 single precision)."""

    size_in_bytes = 4
    alignment = size_in_bytes

    is_fp = True

    def __repr__(self) -> str:
        return "F32"
