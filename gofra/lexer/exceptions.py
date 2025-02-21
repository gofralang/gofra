from gofra.exceptions import GofraError

from .tokens import TokenLocation


class LexerError(GofraError):
    """General error within lexer.

    Should not be used directly as not provides information about error source!
    """

    def __repr__(self) -> str:
        return """General lexer error occurred. 
Please open an issue about that undocumented behavior!
"""


class LexerEmptyInputLinesError(LexerError):
    def __repr__(self) -> str:
        return """No input source text lines. 
Blank source is not allowed within lexer context. 

Did you accidentally pass empty source?"""


class LexerUnclosedCharacterQuoteError(LexerError):
    def __init__(self, *args: object, open_quote_location: TokenLocation) -> None:
        super().__init__(*args)
        self.open_quote_location = open_quote_location

    def __repr__(self) -> str:
        return f"Unclosed character quote at {self.open_quote_location}!"


class LexerEmptyCharacterError(LexerError):
    def __init__(self, *args: object, open_quote_location: TokenLocation) -> None:
        super().__init__(*args)
        self.open_quote_location = open_quote_location

    def __repr__(self) -> str:
        return f"""Empty character at {self.open_quote_location}!
Expected symbol in character!"""


class LexerExcessiveCharacterLengthError(LexerError):
    def __init__(
        self,
        *args: object,
        excess_begins_at: TokenLocation,
        excess_by_count: int,
    ) -> None:
        super().__init__(*args)
        self.excess_begins_at = excess_begins_at
        self.excess_by_count = excess_by_count

    def __repr__(self) -> str:
        return f"""Excessive character at {self.excess_begins_at}!
Expected only one symbol in character but got {self.excess_by_count}!

Did you accidentally mix up characters and strings?"""


class LexerUnclosedStringQuoteError(LexerError):
    def __init__(
        self,
        *args: object,
        open_quote_location: TokenLocation,
    ) -> None:
        super().__init__(*args)
        self.open_quote_location = open_quote_location

    def __repr__(self) -> str:
        return f"Unclosed string quote at {self.open_quote_location}"
