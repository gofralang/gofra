"""Gofra core entry."""

from collections.abc import Iterable
from pathlib import Path

from gofra.consts import GOFRA_ENTRY_POINT
from gofra.context import ProgramContext
from gofra.optimizer import optimize_program
from gofra.parser import parse_file
from gofra.typecheck import validate_type_safety


def process_input_file(
    filepath: Path,
    include_search_directories: Iterable[Path],
    *,
    do_optimize: bool = True,
    do_typecheck: bool = True,
) -> ProgramContext:
    """Core entry for Gofra API.

    Compiles given filepath down to `IR` into `ProgramContext`.
    Maybe assembled into executable via `assemble_executable`
    """
    parser_context, entry_point = parse_file(filepath, include_search_directories)
    context = ProgramContext.from_parser_context(parser_context, entry_point)

    if do_optimize:
        optimize_program(context)

    if do_typecheck:
        validate_type_safety(
            functions={**context.functions, GOFRA_ENTRY_POINT: context.entry_point},
        )

    return context
