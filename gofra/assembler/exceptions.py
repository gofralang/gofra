from typing import Iterable

from gofra.exceptions import GofraError
from gofra.lexer.tokens import Token


class NoToolkitForAssemblingError(GofraError):
    toolkit_required: Iterable[str]

    def __init__(
        self, *args: object, toolkit_required: Iterable[str], token: Token | None = None
    ) -> None:
        super().__init__(*args, token=token)
        self.toolkit_required = toolkit_required

    def __repr__(self) -> str:
        return f"Unable to assemble executable due to not all toolkit installed, required: {','.join(self.toolkit_required)}"


class UnsupportedBuilderOperatingSystemError(GofraError):
    def __repr__(self) -> str:
        return "You are on unsupported operating system to compile that target"
