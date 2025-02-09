from pathlib import Path

from gofra.lexer import tokenize_text
from gofra.linter import linter_validate
from gofra.optimizer import optimize_operators
from gofra.parser import Operator, parse_tokens


def process_input_file(
    filepath: Path,
    *,
    optimize: bool = True,
    linter: bool = True,
) -> list[Operator]:
    with open(filepath, mode="r", encoding="UTF-8") as fd:
        lines = fd.readlines()

    return process_input_lines(
        lines, from_filename=filepath.name, optimize=optimize, linter=linter
    )


def process_input_lines(
    lines: list[str],
    from_filename: str,
    *,
    optimize: bool = True,
    linter: bool = True,
) -> list[Operator]:
    tokens = list(tokenize_text(lines, from_filename))
    operators = parse_tokens(tokens)
    if optimize:
        operators = optimize_operators(operators)
    if linter:
        linter_validate(operators)
    return operators
