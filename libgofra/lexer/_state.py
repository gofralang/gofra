from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .tokens import TokenLocation

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=False)
class LexerState:
    """State for lexical analysis which only required for internal usages."""

    source: Path | Literal["cli", "toolchain"]

    _row: int = 0
    col: int = 0

    _line: str = ""

    def current_location(self) -> TokenLocation:
        """Location of a token at the current cursor position.

        Note that for non-file sources the location still carries a real line/column
        (so error messages are useful), only the origin is different.
        """
        if self.source == "cli":
            return TokenLocation.cli(
                line_number=self.row,
                col_number=self.col,
            )
        if self.source == "toolchain":
            return TokenLocation.toolchain(
                line_number=self.row,
                col_number=self.col,
            )

        return TokenLocation(
            filepath=self.source,
            line_number=self.row,
            col_number=self.col,
        )

    @property
    def row(self) -> int:
        return self._row

    @property
    def line(self) -> str:
        return self._line

    def set_line(self, row: int, line: str) -> None:
        self._row = row
        self._line = line
        self.col = 0
