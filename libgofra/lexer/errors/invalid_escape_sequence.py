from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation


class InvalidEscapeSequenceError(GofraError):
    def __init__(self, at: TokenLocation, sequence: str) -> None:
        self.at = at
        self.sequence = sequence

    def __repr__(self) -> str:
        return f"""Invalid escape sequence at {self.at}!

Encountered unknown or malformed escape sequence: '{self.sequence}'

Supported escape sequences are:
  \\n \\t \\r \\0 \\a \\b \\f \\v \\\\ \\' \\" \\xNN \\uNNNN \\UNNNNNNNN \\NNN

{self.generic_error_name}"""
