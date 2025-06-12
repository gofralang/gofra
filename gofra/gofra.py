"""Gofra core entry."""

from collections.abc import Iterable
from pathlib import Path

from gofra.context import ProgramContext
from gofra.parser import parse_file


def process_input_file(
    filepath: Path,
    include_paths: Iterable[Path],
) -> ProgramContext:
    """Core entry for Gofra API.

    Compiles given filepath down to `IR` into `ProgramContext`.
    Maybe assembled into executable via `assemble_executable`

    Does not provide optimizer or type checker.
    """
    parser_context, entry_point = parse_file(filepath, include_paths)
    return ProgramContext.from_parser_context(parser_context, entry_point)
