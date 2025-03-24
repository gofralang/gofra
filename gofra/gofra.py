from collections.abc import Iterable, Sequence
from pathlib import Path

from gofra.optimizer import optimize_operators
from gofra.parser import Operator, parse_file_into_operators
from gofra.typecheck import validate_type_safety


def process_input_file(
    filepath: Path,
    include_search_directories: Iterable[Path],
    *,
    optimize: bool = True,
    typecheck: bool = True,
) -> Sequence[Operator]:
    operators = parse_file_into_operators(
        filepath,
        include_search_directories=include_search_directories,
    ).operators
    if optimize:
        operators = optimize_operators(operators)
    if typecheck:
        validate_type_safety(operators)
    return operators
