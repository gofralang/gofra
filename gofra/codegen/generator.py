from pathlib import Path
from typing import IO, Callable, assert_never

from gofra.parser.operators import Operator
from gofra.targets import TargetArchitecture, TargetOperatingSystem

from .backends import translate_assembly_arm_macos


def generate_asm(
    asm_filepath: Path,
    operators: list[Operator],
    architecture: TargetArchitecture,
    os: TargetOperatingSystem,
) -> None:
    with open(asm_filepath, mode="w", encoding="UTF-8") as fd:
        translator = _get_translator_for_backend(architecture, os)
        return translator(fd, operators)


def _get_translator_for_backend(
    architecture: TargetArchitecture, os: TargetOperatingSystem
) -> Callable[[IO[str], list[Operator]], None]:
    # TODO!(@kirillzhosul): We currently dont expect nothing from MACOS
    assert os == TargetOperatingSystem.MACOS

    match architecture:
        case TargetArchitecture.ARM:
            return translate_assembly_arm_macos
        case _:
            assert_never(architecture)
