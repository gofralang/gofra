from abc import abstractmethod

from gofra.lexer.tokens import Token


class GofraError(Exception):
    token: Token | None = None

    def __init__(self, *args: object, token: Token | None = None) -> None:
        super().__init__(*args)
        self.token = token

    @abstractmethod
    def __repr__(self) -> str:
        return f"Some internal error occurred ({super().__repr__()}), that is currently not documented"
