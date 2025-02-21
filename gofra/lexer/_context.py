from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .exceptions import LexerEmptyInputLinesError
from .tokens import TokenLocation


@dataclass(frozen=False)
class LexerContext:
    """Context for lexical analysis which only required from internal usages."""

    source_filepath: Path
    lines: Sequence[str]

    row_end: int
    col_end: int = 0

    row: int = 0
    col: int = 0

    line: str = ""

    def __post_init__(self) -> None:
        if not self.row_end:
            raise LexerEmptyInputLinesError

    def row_is_consumed(self) -> bool:
        return self.row >= self.row_end

    def col_is_consumed(self) -> bool:
        return self.col >= self.col_end

    def current_location(self) -> TokenLocation:
        return TokenLocation(
            filepath=self.source_filepath,
            line_number=self.row,
            col_number=self.col,
        )
