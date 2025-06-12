from sys import stderr, stdout
from typing import Literal

type MessageLevel = Literal["INFO", "ERROR", "WARNING"]


def cli_message(level: MessageLevel, text: str, *, verbose: bool = True) -> None:
    """Emit an message to CLI user with given level, applying FD according to level."""
    fd = stdout if level not in ("ERROR",) else stderr

    if level == "INFO" and not verbose:
        return
    print(f"[{level}] {text}", file=fd)
