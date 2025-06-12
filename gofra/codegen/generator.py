from pathlib import Path

from gofra.codegen.targets import TARGET_T
from gofra.context import ProgramContext

from .get_backend import get_backend_for_target


def generate_code_for_assembler(
    output_path: Path,
    context: ProgramContext,
    target: TARGET_T,
) -> None:
    """Generate assembly from given program context and specified ARCHxOS pair into given file."""
    backend = get_backend_for_target(target)

    output_path.parent.mkdir(exist_ok=True)
    with output_path.open(
        mode="w",
        errors="strict",
        buffering=1,
        newline="",
        encoding="UTF-8",
    ) as fd:
        return backend(fd, context)
