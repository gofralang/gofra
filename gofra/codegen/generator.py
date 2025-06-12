from pathlib import Path

from gofra.codegen.targets import TargetArchitecture, TargetOperatingSystem
from gofra.context import ProgramContext

from .get_backend import get_backend_for_target_pair


def generate_code_for_assembler(
    output_path: Path,
    context: ProgramContext,
    architecture: TargetArchitecture,
    operating_system: TargetOperatingSystem,
) -> None:
    """Generate assembly from given program context and specified ARCHxOS pair into given file."""
    backend = get_backend_for_target_pair(architecture, operating_system)

    output_path.parent.mkdir(exist_ok=True)
    with output_path.open(
        mode="w",
        errors="strict",
        buffering=1,
        newline="",
        encoding="UTF-8",
    ) as fd:
        return backend(fd, context)
