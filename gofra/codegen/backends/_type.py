from typing import IO, Protocol

from gofra.context import ProgramContext


class CodeGeneratorBackend(Protocol):
    def __call__(
        self,
        fd: IO[str],
        program_context: ProgramContext,
        *,
        debug_comments: bool,
    ) -> None: ...
