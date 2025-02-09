from gofra.exceptions import GofraError
from gofra.lexer.tokens import Token


class ParserError(GofraError): ...


class ParserEmptyInputTokensError(ParserError): ...


class ParserUnknownWordError(ParserError):
    def __init__(self, *args: object, token: Token) -> None:
        super().__init__(*args, token=token)

    def __repr__(self) -> str:
        assert self.token
        location = self.token.location
        return f"Unknown word `{self.token.text}` in {location[0]} on {location[1]}:{location[2]}"


class ParserNoWhileBeforeDoError(ParserError): ...


class ParserNoIfBeforeElseError(ParserError): ...


class ParserElseAfterNonIfError(ParserError): ...


class ParserContextNotClosedError(ParserError): ...


class ParserEndWithoutContextError(ParserError): ...


class ParserEndAfterWhileError(ParserError): ...
