from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation


class InvalidNumberLiteralError(GofraError):
    def __init__(self, at: TokenLocation, number_raw: str, reason: str) -> None:
        self.at = at
        self.number_raw = number_raw
        self.reason = reason

    def __repr__(self) -> str:
        return f"""Invalid number literal at {self.at}!

Invalid number: '{self.number_raw}'
Reason: {self.reason}

Numbers must be one of:
  123  -123  1_000  0x1F  0b1010  0o777  1.5  1.5e10  1.5e-10

{self.generic_error_name}"""
