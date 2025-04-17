from pathlib import Path

from gofra.context import ProgramContext
from gofra.targets import TargetArchitecture, TargetOperatingSystem

from .get_backend import get_backend_for_target_pair


def generate_code_for_assembler(
    output_path: Path,
    context: ProgramContext,
    architecture: TargetArchitecture,
    operating_system: TargetOperatingSystem,
    *,
    debug_comments: bool = True,
) -> None:
    backend = get_backend_for_target_pair(architecture, operating_system)

    output_path.parent.mkdir(exist_ok=True)
    with output_path.open(
        mode="w",
        errors="strict",
        buffering=1,
        newline="",
        encoding="UTF-8",
    ) as fd:
        return backend(fd, context, debug_comments=debug_comments)
