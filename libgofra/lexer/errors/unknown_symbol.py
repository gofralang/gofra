from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation


class UnknownSymbolError(GofraError):
    def __init__(self, at: TokenLocation, symbol: str) -> None:
        self.at = at
        self.symbol = symbol

    def __repr__(self) -> str:
        return f"""Unknown symbol at {self.at}!

Encountered symbol '{self.symbol}' that is not known to the language

{self.generic_error_name}"""
