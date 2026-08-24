"""Assembler module to assemble programs in Gofra language into executables."""

from __future__ import annotations

from collections.abc import Iterable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import TYPE_CHECKING

from libgofra.assembler.drivers._get_assembler_driver import get_assembler_driver

if TYPE_CHECKING:
    from pathlib import Path
    from subprocess import CompletedProcess

    from libgofra.assembler.drivers import AssemblerDriverProtocol
    from libgofra.targets import Target


def assemble_object_file(  # noqa: PLR0913
    in_assembly_file: Path,
    out_object_file: Path,
    target: Target,
    *,
    debug_information: bool,
    extra_flags: list[str] | None = None,
    driver: AssemblerDriverProtocol | None = None,
) -> CompletedProcess[bytes]:
    """Assemble given assembly file into object file using assembler driver.

    You supposed to handle errors by assembler via returned process information

    :param target: Compilation target
    :param in_assembly_file: Path to assembly file as input
    :param out_object_file: Path to object file as output
    :param debug_information: If specified, will pass debug info flag to assembler and specify its version
    :param extra_flags: Any additional flags

    :raises NoAssemblerDriverError: If no suitable driver found
    """
    return assemble_object_files(
        [(in_assembly_file, out_object_file)],
        target=target,
        debug_information=debug_information,
        extra_flags=extra_flags,
        driver=driver,
        max_workers=1,
    )[0]


def assemble_object_files(  # noqa: PLR0913
    file_pairs: Iterable[tuple[Path, Path]],
    target: Target,
    *,
    debug_information: bool,
    extra_flags: list[str] | None = None,
    driver: AssemblerDriverProtocol | None = None,
    max_workers: int = 4,
) -> list[CompletedProcess[bytes]]:
    """Assemble given assembly files into object files using assembler driver.

    You supposed to handle errors by assembler via returned process information
    Submits process jobs via threadpool executor, and result is list of these processes

    Configuration (debug info, flags) applied to all of the pairs given

    :param target: Compilation target
    :param in_assembly_file: Path to assembly file as input
    :param out_object_file: Path to object file as output
    :param debug_information: If specified, will pass debug info flag to assembler and specify its version
    :param extra_flags: Any additional flags

    :raises NoAssemblerDriverError: If no suitable driver found
    """
    driver = driver or get_assembler_driver(target)
    flags = extra_flags or []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                driver.assemble,
                target=target,
                in_assembly_file=in_assembly_file,
                out_object_file=out_object_file,
                debug_information=debug_information,
                flags=flags,
            )
            for in_assembly_file, out_object_file in file_pairs
        ]

        return [f.result() for f in futures]
