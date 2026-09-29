import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from dataclasses import dataclass
from typing import NoReturn

from libgofra import __build_date__, __commit__, __version__
from libgofra.targets.infer_host import infer_host_target


@dataclass(slots=True, frozen=True)
class VersionArguments:
    verbose: bool


def parse_arguments(namespace: Namespace) -> VersionArguments:
    return VersionArguments(
        verbose=bool(namespace.verbose),
    )


def build_parser(subparsers: "_SubParsersAction[ArgumentParser]") -> ArgumentParser:
    parser = subparsers.add_parser(
        "version",
        help="Show version",
        description="Show detailed build information",
        allow_abbrev=False,
    )

    parser.add_argument(
        "-v",
        required=False,
        action="store_true",
        help="Display git build commit/date",
        dest="verbose",
    )
    return parser


def execute(args: VersionArguments) -> NoReturn:
    """Perform version command goal that display information version of the compiler."""
    host_target = infer_host_target()
    host_target_simple = host_target.simple_name if host_target else "unknown/unknown"

    version = __version__

    print(f"gofra {version} {host_target_simple}")

    if args.verbose:
        print(f"commit: {__commit__}")
        print(f"built: {__build_date__}")

    return sys.exit(0)
