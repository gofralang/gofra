from enum import IntEnum, auto


class GofraType(IntEnum):
    """Types that are defined within language so we can check type safety."""

    # Number which size is infered from target backend (mostly 32/64 bits architectures)
    INTEGER = auto()

    # Infer integer as pointer for pointer arithmetics typecheck and FFI
    POINTER = auto()

    # Infer integer as boolean or result from comparsion
    BOOLEAN = auto()

    # Used to specify that function returns nothing
    VOID = auto()

    # Typechecker only!
    ANY = auto()

    def __repr__(self) -> str:
        return self.name


WORD_TO_GOFRA_TYPE = {
    "int": GofraType.INTEGER,
    "ptr": GofraType.POINTER,
    "bool": GofraType.BOOLEAN,
    "void": GofraType.VOID,
}
