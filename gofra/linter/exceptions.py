from gofra.exceptions import GofraError
from gofra.lexer.tokens import Token


class LinterError(GofraError): ...


class LinterEmptyInputOperators(LinterError): ...


class LinterAmbiguousStackAtEndError(LinterError):
    def __repr__(self) -> str:
        assert self.token
        return f"There is non-empty stack at linter stage! Last insertion to stack encountered at {self.token.location}"


class LinterPopFromEmptyStackError(LinterError):
    def __init__(self, *args: object, underflow_size: int, token: Token) -> None:
        super().__init__(*args, token=token)
        self.underflow_size = underflow_size

    def __repr__(self) -> str:
        assert self.token
        return f"Tried to pop from empty stack at {self.token.location} within `{self.token.text}`, required {self.underflow_size} more items!"


class LinterWrongTypecheckError(LinterError): ...
