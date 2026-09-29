import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from gofra.cache.directory import cleanup_build_cache_directory

# TODO(@kirillzhosul): --dry-run
# TODO(@kirillzhosul): --verbose
# TODO(@kirillzhosul): proper cleaning
# TODO(@kirillzhosul): what to clean


@dataclass(slots=True, frozen=True)
class CleanArguments:
    cache_dir: Path


def parse_arguments(namespace: Namespace) -> CleanArguments:
    return CleanArguments(cache_dir=Path(namespace.cache_dir))


def build_parser(subparsers: "_SubParsersAction[ArgumentParser]") -> ArgumentParser:
    parser = subparsers.add_parser(
        "clean",
        help="Clean build cache and artifacts",
        description="Remove build cache and intermediate artifacts from build cache directory",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path("./.build"),
        help="Cache directory (default: ./.build)",
        dest="cache_dir",
    )

    return parser


def execute(args: CleanArguments) -> NoReturn:
    """Perform clean command goal that cleans build caches."""
    cache_dir = args.cache_dir

    if not cache_dir.exists():
        print(f"Nothing to clean: {cache_dir} does not exist")
        return sys.exit(0)

    if not cache_dir.is_dir():
        print(f"Nothing to clean: {cache_dir} not a directory")
        return sys.exit(0)

    cleanup_build_cache_directory(cache_dir)
    print(f"Cleaned: {cache_dir}")

    return sys.exit(0)
