from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation


class IndexOutOfBoundError(GofraError):
    def __init__(
        self,
        index: int,
        bound: int,
        at: TokenLocation,
    ) -> None:
        self.index = index
        self.at = at
        self.bound = bound

    def __repr__(self) -> str:
        valid = (
            f", valid: 0..{self.bound - 1}"
            if self.bound > 0
            else ", no possible values"
        )
        return f"""Index {self.index} is out of bounds (size: {self.bound}{valid}) at {self.at}

{self.generic_error_name}"""
