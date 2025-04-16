from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from platform import system as current_platform_system

from gofra.cli.output import cli_message
from gofra.targets import TargetArchitecture, TargetOperatingSystem


@dataclass(frozen=True)
class CLIArguments:
    filepath: Path
    filepath_output: Path

    action_compile: bool

    execute_after_compile: bool
    fall_into_debugger: bool

    include_search_directories: list[Path]

    target_os: TargetOperatingSystem
    target_architecture: TargetArchitecture

    no_optimizations: bool
    no_typecheck: bool

    build_cache_directory: Path | None
    build_cache_delete_after_run: bool


def parse_cli_arguments() -> CLIArguments:
    args = _construct_argument_parser().parse_args()
    filepath_output = (
        Path(args.output) if args.output else _output_filename_fallback(Path(args.file))
    )
    if None in args.include_search_dir:
        cli_message(
            level="WARNING",
            text="One of the include search directories is empty, skipping...",
        )

    return CLIArguments(
        filepath=Path(args.file),
        fall_into_debugger=bool(args.fall_into_debugger),
        filepath_output=filepath_output,
        action_compile=bool(args.compile),
        execute_after_compile=bool(args.execute),
        build_cache_delete_after_run=bool(args.delete_cache),
        build_cache_directory=Path(args.cache_dir) if args.cache_dir else None,
        target_architecture=TargetArchitecture.ARM,
        target_os=TargetOperatingSystem.MACOS,
        no_optimizations=bool(args.no_optimizations),
        no_typecheck=bool(args.no_typecheck),
        include_search_directories=[
            Path(args.file).parent,
            Path("./"),
            *map(Path, [a for a in args.include_search_dir if a]),
        ],
    )


def _construct_argument_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Gofra Toolkit - CLI for working with Gofra programming language",
    )

    parser.add_argument("file", type=str, help="The input file")

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--compile",
        "-c",
        action="store_true",
        help="Compile the file into executable",
    )

    parser.add_argument(
        "--include-search-dir",
        "-isd",
        required=False,
        help="Directories to search for include files",
        action="append",
        nargs="?",
        default=["./", "./lib"],
    )

    parser.add_argument(
        "--execute",
        "-e",
        required=False,
        action="store_true",
        help="If given, will execute output after run",
    )

    parser.add_argument(
        "--fall-into-debugger",
        "-dbg",
        action="store_true",
        required=False,
        help="If passed, will run debugger after compile",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=False,
        help="Path to output file which will be generated",
    )

    parser.add_argument(
        "--cache-dir",
        "-cd",
        type=str,
        default="./.build",
        required=False,
        help="Path to directory where to store cache (defaults to current directory)",
    )
    parser.add_argument(
        "--delete-cache",
        "-dc",
        action="store_true",
        required=False,
        help="If passed, will delete cache after run",
    )

    parser.add_argument(
        "--no-optimizations",
        "-no",
        action="store_true",
        required=False,
        help="If passed, will disable optimizer",
    )

    parser.add_argument(
        "--no-typecheck",
        "-nt",
        action="store_true",
        required=False,
        help="If passed, will disable type checking",
    )

    return parser


def _output_filename_fallback(input_filepath: Path) -> Path:
    assert current_platform_system() == "Darwin"
    if input_filepath.suffix == "":
        return input_filepath.with_suffix(input_filepath.suffix + "._")
    return input_filepath.with_suffix("")
