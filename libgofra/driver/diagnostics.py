from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence


class DiagnosticConsumer(Protocol):
    """Sink for compiler messages, timings, and subprocess commands."""

    def info(self, text: str) -> None: ...

    def warning(self, text: str) -> None: ...

    def command(self, argv: Sequence[str]) -> None: ...

    @contextmanager
    def timer(self, label: str) -> Generator[None]: ...


class NullDiagnosticConsumer:
    """Silent consumer, for tests and dry runs."""

    def info(self, text: str) -> None:
        _ = text

    def warning(self, text: str) -> None:
        _ = text

    def command(self, argv: Sequence[str]) -> None:
        _ = argv

    @contextmanager
    def timer(self, label: str) -> Generator[None]:
        _ = label
        yield
