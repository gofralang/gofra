from enum import IntEnum, auto


class GofraType(IntEnum):
    """Types that are defined within language so we can check type safety."""

    INTEGER = auto()
    POINTER = auto()
    BOOLEAN = auto()
    VOID = auto()


WORD_TO_GOFRA_TYPE = {
    "int": GofraType.INTEGER,
    "ptr": GofraType.POINTER,
    "bool": GofraType.BOOLEAN,
    "void": GofraType.VOID,
}
