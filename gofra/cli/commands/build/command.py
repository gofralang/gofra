import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from typing import NoReturn

from gofra.cli.errors.error_handler import cli_gofra_error_handler

from . import groups
from .arguments import BuildArguments
from .goals import perform_desired_toolchain_goal
from .parser import parse_cli_arguments


def parse_arguments(namespace: Namespace) -> BuildArguments:
    return parse_cli_arguments(namespace)


def build_parser(subparsers: "_SubParsersAction[ArgumentParser]") -> ArgumentParser:
    parser = subparsers.add_parser(
        "build",
        help="Compile Gofra source files",
        description="Compile Gofra source files into executable, object, or library",
        allow_abbrev=False,
    )

    parser.add_argument(
        "source_files",
        help="Input source code files in Gofra to process (`.gof` files)",
        nargs="*",
        default=[],
    )

    groups.add_target_group(parser)
    groups.add_output_group(parser)
    groups.add_logging_group(parser)

    groups.add_debug_group(parser)
    groups.add_preprocessor_group(parser)
    groups.add_cache_group(parser)
    groups.add_linker_group(parser)
    groups.add_optimizer_group(parser)
    groups.add_toolchain_debug_group(parser)
    groups.add_codegen_group(parser)
    groups.add_additional_group(parser)
    return parser


def execute(args: BuildArguments) -> NoReturn:
    wrapper = cli_gofra_error_handler(
        debug_user_friendly_errors=args.cli_debug_user_friendly_errors,
    )

    with wrapper:
        # Wrap goal into error handler as in unwraps errors into user-friendly ones (except internal ones as bugs)
        perform_desired_toolchain_goal(args)
    return sys.exit(0)
