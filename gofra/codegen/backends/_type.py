from collections.abc import Sequence
from typing import IO, Protocol

from gofra.parser.operators import Operator


class CodeGeneratorBackend(Protocol):
    def __call__(
        self,
        fd: IO[str],
        operators: Sequence[Operator],
        *,
        debug_comments: bool,
    ) -> None: ...
