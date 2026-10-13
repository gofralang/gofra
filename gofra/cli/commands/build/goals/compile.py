from __future__ import annotations

import sys
from typing import TYPE_CHECKING, NoReturn

from gofra.cli.commands.build.arguments import BuildOutputFormat
from gofra.cli.driver_diag import CliDiagnosticConsumer
from gofra.cli.output import cli_message
from gofra.execution.permissions import apply_file_executable_permissions
from libgofra.driver.artifact import (
    Artifact,
    AssemblyArtifact,
    ExecutableArtifact,
    LibraryArtifact,
    ObjectArtifact,
)
from libgofra.driver.cache.directory import prepare_build_cache_directory
from libgofra.driver.driver import Driver

if TYPE_CHECKING:
    from pathlib import Path

    from gofra.cli.commands.build.arguments import BuildArguments


def cli_perform_compile_goal(args: BuildArguments) -> NoReturn:
    """Process full toolchain onto input source files."""
    prepare_build_cache_directory(args.build_cache_dir)

    # Actually this can be skipped if we identify that some modules does not needs rebuild
    # We may skip this part also if identify that final build artifact is not needs rebuild
    # e.g if dependant object files is already linked against this artifact (modify time, hash)
    diag = CliDiagnosticConsumer(
        verbose=args.verbose,
        show_commands=args.show_commands,
    )

    driver = Driver(
        request=args.to_compilation_request(),
        diag=diag,
    )
    artifact = driver.run()

    if isinstance(artifact, ExecutableArtifact):
        apply_file_executable_permissions(args.output_filepath)

    if args.output_format == BuildOutputFormat.OBJECT:
        driver.layout.root_object.replace(args.output_filepath)
    elif args.output_format == BuildOutputFormat.ASSEMBLY:
        driver.layout.root_assembly.replace(args.output_filepath)

    cli_message(
        level="INFO",
        text=f"Compiled input file down to {args.output_format.name} `{args.output_filepath.name}`!",
        verbose=args.verbose,
    )

    _cleanup_cache_gc(artifact, args)
    return sys.exit(0)


def _cleanup_cache_gc(artifact: Artifact, args: BuildArguments) -> None:
    if not args.delete_build_cache:
        return
    paths: set[Path] = set()
    if isinstance(artifact, (ExecutableArtifact, LibraryArtifact)):
        paths |= set(artifact.objects.modules_objects.values())
        paths |= set(artifact.objects.assembly.modules_assembly.values())
    elif isinstance(artifact, ObjectArtifact):
        paths |= set(artifact.modules_objects.values())
        paths |= set(artifact.assembly.modules_assembly.values())
    elif isinstance(artifact, AssemblyArtifact):
        paths |= set(artifact.modules_assembly.values())
    cli_message(
        level="INFO",
        text=f"Cleaning up {len(paths)} cache files...",
        verbose=args.verbose,
    )
    for p in paths:
        p.unlink(missing_ok=True)
