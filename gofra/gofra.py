from pathlib import Path

from gofra.lexer import tokenize_text
from gofra.parser import Operator, parse_tokens


def parse_and_tokenize_input_file(filepath: Path) -> list[Operator]:
    with open(filepath, mode="r", encoding="UTF-8") as fd:
        lines = fd.readlines()

    return parse_and_tokenize_input_lines(lines, from_filename=filepath.name)


def parse_and_tokenize_input_lines(
    lines: list[str], from_filename: str
) -> list[Operator]:
    tokens = list(tokenize_text(lines, from_filename))
    return parse_tokens(tokens)
