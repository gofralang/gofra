from collections.abc import Iterable
from pathlib import Path

from gofra.context import ProgramContext
from gofra.optimizer import optimize_operators
from gofra.parser import parse_file_into_operators
from gofra.typecheck import validate_type_safety


def process_input_file(
    filepath: Path,
    include_search_directories: Iterable[Path],
    *,
    optimize: bool = True,
    typecheck: bool = True,
) -> ProgramContext:
    parse_context = parse_file_into_operators(
        filepath,
        include_search_directories=include_search_directories,
    )

    context = ProgramContext(
        functions=parse_context.functions,
        operators=parse_context.operators,
    )

    if optimize:
        context.operators = optimize_operators(context.operators)  # type: ignore  # noqa: PGH003
    if typecheck:
        validate_type_safety(context.operators)

    return context
