from __future__ import annotations

import sys
from pathlib import Path
from platform import system as current_platform_system
from shutil import which
from subprocess import CalledProcessError, check_output
from typing import TYPE_CHECKING

from gofra.cli.output import cli_message
from gofra.codegen import generate_code_for_assembler
from gofra.targets import TargetArchitecture, TargetOperatingSystem

from .exceptions import (
    NoToolkitForAssemblingError,
    UnsupportedBuilderOperatingSystemError,
)

if TYPE_CHECKING:
    from gofra.context import ProgramContext


def assemble_executable(  # noqa: PLR0913
    context: ProgramContext,
    output: Path,
    architecture: TargetArchitecture,
    os: TargetOperatingSystem,
    propagated_linker_flags: list[str],
    *,
    build_cache_directory: Path | None = None,
    build_cache_delete_after_end: bool = False,
) -> None:
    _validate_toolkit_installation()

    _prepare_build_cache_directory(
        build_cache_directory=build_cache_directory,
    )

    asm_filepath = _generate_asm(
        context,
        output,
        architecture,
        os,
        build_cache_directory=build_cache_directory,
    )

    o_filepath = _assemble_object_file(
        output,
        architecture,
        asm_filepath,
        build_cache_directory=build_cache_directory,
    )

    _link_final_executable(
        output,
        architecture,
        os,
        o_filepath,
        propagated_linker_flags=propagated_linker_flags,
    )

    if build_cache_delete_after_end:
        asm_filepath.unlink()
        o_filepath.unlink()


def _prepare_build_cache_directory(build_cache_directory: Path | None) -> None:
    if build_cache_directory is None or build_cache_directory.exists():
        return

    build_cache_directory.mkdir(exist_ok=False)

    with (build_cache_directory / ".gitignore").open("w") as f:
        f.write("# Do not include this newly generated build cache into git VCS\n")
        f.write("*\n")


def _link_final_executable(
    output: Path,
    architecture: TargetArchitecture,
    os: TargetOperatingSystem,
    o_filepath: Path,
    propagated_linker_flags: list[str],
) -> None:
    match current_platform_system():
        case "Darwin":
            assert architecture == TargetArchitecture.ARM
            assert os == TargetOperatingSystem.MACOS

            system_sdk = Path(
                check_output(  # noqa: S603
                    ["/usr/bin/xcrun", "-sdk", "macosx", "--show-sdk-path"],
                    text=True,
                ).strip(),
            )

            check_output(  # noqa: S603
                [
                    "/usr/bin/ld",
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
                    *propagated_linker_flags,
                ],
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
            if architecture != TargetArchitecture.ARM:
                raise UnsupportedBuilderOperatingSystemError

            command = [
                "/usr/bin/as",
                "-arch",
                "arm64",
                "-o",
                str(o_filepath),
                str(asm_filepath),
            ]
            try:
                check_output(command)  # noqa: S603
            except CalledProcessError as e:
                cli_message(
                    "ERROR",
                    "Failed to generate binary from output assembly, "
                    f"error code: {e.returncode}",
                )
                sys.exit(1)
        case _:
            raise UnsupportedBuilderOperatingSystemError

    return o_filepath


def _generate_asm(
    context: ProgramContext,
    output: Path,
    architecture: TargetArchitecture,
    os: TargetOperatingSystem,
    *,
    build_cache_directory: Path | None = None,
) -> Path:
    asm_filepath = build_cache_directory / "build" if build_cache_directory else output
    asm_filepath = asm_filepath.with_suffix(".s")

    generate_code_for_assembler(asm_filepath, context, architecture, os)
    return asm_filepath


def _validate_toolkit_installation() -> None:
    match current_platform_system():
        case "Darwin":
            required_toolkit = ("as", "ld", "xcrun")

            toolkit = {(tk, which(tk) is not None) for tk in required_toolkit}
            missing_toolkit = {
                tk for (tk, tk_is_installed) in toolkit if not tk_is_installed
            }
            if missing_toolkit:
                raise NoToolkitForAssemblingError(toolkit_required=missing_toolkit)
        case _:
            raise UnsupportedBuilderOperatingSystemError
