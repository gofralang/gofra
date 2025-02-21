from collections.abc import Sequence
from pathlib import Path

from gofra.optimizer import optimize_operators
from gofra.parser import Operator, parse_file_into_operators
from gofra.typecheck import validate_type_safety


def process_input_file(
    filepath: Path,
    *,
    optimize: bool = True,
    linter: bool = True,
) -> Sequence[Operator]:
    operators = parse_file_into_operators(filepath).operators
    if optimize:
        operators = optimize_operators(operators)
    if linter:
        validate_type_safety(operators)
    return operators
