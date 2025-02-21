from sys import stderr, stdout
from typing import Literal

type MessageLevel = Literal["INFO", "ERROR"]


def cli_message(level: MessageLevel, text: str) -> None:
    fd = stdout if level not in ("ERROR",) else stderr
    print(f"[{level}] {text}", file=fd)
