"""Gofra core entry."""

from collections.abc import Iterable
from pathlib import Path

from gofra.consts import GOFRA_ENTRY_POINT
from gofra.context import ProgramContext
from gofra.optimizer import optimize_program
from gofra.parser import parse_file_into_operators
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
    parse_context = parse_file_into_operators(
        filepath,
        include_search_directories=include_search_directories,
    )

    assert GOFRA_ENTRY_POINT in parse_context.functions
    context = ProgramContext(
        functions=parse_context.functions,
        memories=parse_context.memories,
        entry_point=parse_context.functions.pop(GOFRA_ENTRY_POINT),
    )

    if do_optimize:
        optimize_program(context)

    if do_typecheck:
        validate_type_safety(
            entry_point=context.entry_point,
            functions=context.functions,
        )

    return context
