# from os import system
from pathlib import Path
from platform import system as current_platform_system
from shutil import which
from subprocess import check_output

from gofra.codegen import TargetArchitecture, generate_asm
from gofra.parser.operators import Operator
from gofra.targets import TargetOperatingSystem

from .exceptions import (
    NoToolkitForAssemblingError,
    UnsupportedBuilderOperatingSystemError,
)


def assemble_executable(
    operators: list[Operator],
    output: Path,
    architecture: TargetArchitecture,
    os: TargetOperatingSystem,
    *,
    build_cache_directory: Path | None = None,
    build_cache_delete_after_end: bool = False,
) -> None:
    _validate_toolkit_installation()
    if build_cache_directory:
        build_cache_directory.mkdir(exist_ok=True)
    asm_filepath = _generate_asm(
        operators, output, architecture, os, build_cache_directory=build_cache_directory
    )

    o_filepath = _assemble_object_file(
        output, architecture, asm_filepath, build_cache_directory=build_cache_directory
    )

    _link_final_executable(output, architecture, os, o_filepath)

    if build_cache_delete_after_end:
        asm_filepath.unlink()
        o_filepath.unlink()


def _link_final_executable(
    output: Path,
    architecture: TargetArchitecture,
    os: TargetOperatingSystem,
    o_filepath: Path,
) -> None:
    match current_platform_system():
        case "Darwin":
            assert architecture == TargetArchitecture.ARM
            assert os == TargetOperatingSystem.MACOS

            system_sdk = Path(
                check_output(
                    ["xcrun", "-sdk", "macosx", "--show-sdk-path"], text=True
                ).strip()
            )

            check_output(
                [
                    "ld",
                    "-o",
                    output,
                    o_filepath,
                    "-e",
                    "_start",
                    "-arch",
                    "arm64",
                    "-lSystem",
                    "-syslibroot",
                    system_sdk,
                ]
            )
        case _:
            raise UnsupportedBuilderOperatingSystemError


def _assemble_object_file(
    output: Path,
    architecture: TargetArchitecture,
    asm_filepath: Path,
    *,
    build_cache_directory: Path | None = None,
) -> Path:
    o_filepath = build_cache_directory / "build" if build_cache_directory else output
    o_filepath = o_filepath.with_suffix(".o")

    match current_platform_system():
        case "Darwin":
            assert architecture == TargetArchitecture.ARM
            check_output(["as", "-arch", "arm64", "-o", o_filepath, asm_filepath])
        case _:
            raise UnsupportedBuilderOperatingSystemError

    return o_filepath


def _generate_asm(
    operators: list[Operator],
    output: Path,
    architecture: TargetArchitecture,
    os: TargetOperatingSystem,
    *,
    build_cache_directory: Path | None = None,
) -> Path:
    asm_filepath = build_cache_directory / "build" if build_cache_directory else output
    asm_filepath = asm_filepath.with_suffix(".s")

    generate_asm(asm_filepath, operators, architecture, os)
    return asm_filepath


def _validate_toolkit_installation() -> None:
    match current_platform_system():
        case "Darwin":
            required_toolkit = ("as", "ld", "xcrun")

            toolkit = set([(tk, which(tk) is not None) for tk in required_toolkit])
            missing_toolkit = {
                tk for (tk, tk_is_installed) in toolkit if not tk_is_installed
            }
            if missing_toolkit:
                raise NoToolkitForAssemblingError(toolkit_required=missing_toolkit)
        case _:
            raise UnsupportedBuilderOperatingSystemError
