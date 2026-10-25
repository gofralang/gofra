from libgofra.hir.operator import TypecastMeta
from libgofra.types import BoolType, PointerType, Type
from libgofra.types.primitive import CharType
from libgofra.types.primitive.floats import F64Type
from libgofra.types.primitive.integers import IntegerType


def resolve_type_cast_to_kind(source: Type, target: Type) -> TypecastMeta.Kind | None:  # noqa: PLR0911
    """Resolve type cast kind required to cast type `source` into type `target`, possibly losing information."""
    a, b = source, target

    if isinstance(a, PointerType) and isinstance(b, PointerType):
        # *T -> *T
        return TypecastMeta.Kind.REINTERPRET

    if (
        isinstance(a, IntegerType)
        and isinstance(b, PointerType)
        and a.size_in_bytes == b.size_in_bytes
    ):
        # int -> *T
        return TypecastMeta.Kind.REINTERPRET

    if (
        isinstance(a, PointerType)
        and isinstance(b, IntegerType)
        and b.size_in_bytes == b.size_in_bytes
    ):
        # *T -> int
        return TypecastMeta.Kind.REINTERPRET

    if isinstance(a, IntegerType) and isinstance(b, BoolType):
        # int -> bool
        return TypecastMeta.Kind.NORMALIZE_BOOL

    if isinstance(a, BoolType) and isinstance(b, IntegerType):
        # bool -> int
        return TypecastMeta.Kind.REINTERPRET

    if isinstance(a, (IntegerType, CharType)) and isinstance(
        b,
        (IntegerType, CharType),
    ):
        if a.size_in_bytes > b.size_in_bytes:
            return TypecastMeta.Kind.TRUNCATE  # i64 -> i8
        if a.size_in_bytes < b.size_in_bytes:
            return TypecastMeta.Kind.EXTEND  # i8 -> i64
        return TypecastMeta.Kind.REINTERPRET

    if isinstance(a, IntegerType) and isinstance(b, F64Type):
        return TypecastMeta.Kind.INT_TO_FLOAT
    if isinstance(a, F64Type) and isinstance(b, (IntegerType, CharType)):
        return TypecastMeta.Kind.FLOAT_TO_INT
    if isinstance(a, F64Type) and isinstance(b, BoolType):
        return TypecastMeta.Kind.NORMALIZE_BOOL
    if isinstance(a, F64Type) and isinstance(b, F64Type):
        return TypecastMeta.Kind.REINTERPRET
    return None
