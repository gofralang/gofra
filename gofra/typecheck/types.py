from enum import IntEnum, auto


class GofraType(IntEnum):
    """Types that are defined within language so we can check type safety."""

    INTEGER = auto()
    POINTER = auto()
    BOOLEAN = auto()
