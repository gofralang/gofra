from collections.abc import Generator, Sequence
from contextlib import contextmanager
from time import perf_counter_ns

from gofra.cli.output import cli_message
from libgofra.driver.diagnostics import DiagnosticConsumer


class CliDiagnosticConsumer(DiagnosticConsumer):
    def __init__(self, *, verbose: bool, show_commands: bool) -> None:
        self._verbose = verbose
        self._show_commands = show_commands

    def info(self, text: str) -> None:
        cli_message("INFO", text, verbose=self._verbose)

    def warning(self, text: str) -> None:
        cli_message("WARNING", text)

    def command(self, argv: Sequence[str]) -> None:
        if not self._show_commands:
            return
        cli_message("CMD", " ".join(map(str, argv)))

    @contextmanager
    def timer(self, label: str) -> Generator[None]:
        start = perf_counter_ns()
        yield
        took = (perf_counter_ns() - start) / 1_000_000_000
        if self._verbose:
            cli_message("INFO", f"{label} took {took:.2f}s")
