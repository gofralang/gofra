import contextlib
import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from dataclasses import dataclass
from typing import NoReturn

from gofra.cli.commands.build import groups
from gofra.cli.commands.build.arguments import BuildArguments
from gofra.cli.commands.build.goals.compile import (
    cli_perform_compile_goal,
    log_command,
    wrap_with_perf_time_taken,
)
from gofra.cli.commands.build.parser import parse_cli_arguments
from gofra.cli.errors.error_handler import cli_gofra_error_handler
from gofra.cli.is_segmentation_fault import is_segmentation_fault
from gofra.cli.output import cli_fatal_abort, cli_message
from gofra.execution.execution import execute_native_binary_executable
from libgofra.targets.infer_host import infer_host_target


@dataclass(frozen=True)
class RunArguments:
    parent: BuildArguments
    propagate_execute_child_exit_code: bool


def parse_arguments(namespace: Namespace) -> RunArguments:
    return RunArguments(
        parent=parse_cli_arguments(namespace),
        propagate_execute_child_exit_code=bool(
            namespace.propagate_execute_child_exit_code,
        ),
    )


def build_parser(subparsers: "_SubParsersAction[ArgumentParser]") -> ArgumentParser:
    parser = subparsers.add_parser(
        "run",
        help="Compile and run Gofra source files",
        description="Compile and run Gofra source files",
        allow_abbrev=False,
    )

    parser.add_argument(
        "source_files",
        help="Input source code files in Gofra to process (`.gof` files)",
        nargs="*",
        default=[],
    )

    parser.add_argument(
        "--propagate-execute-child-exit-code",
        "--prop-child-ec",
        required=False,
        action="store_true",
        help="If specified, will propagate exit status of child to parent compiler process",
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


def execute(args: RunArguments) -> NoReturn:
    wrapper = cli_gofra_error_handler(
        debug_user_friendly_errors=args.parent.cli_debug_user_friendly_errors,
    )

    with wrapper:
        # Wrap goal into error handler as in unwraps errors into user-friendly ones (except internal ones as bugs)
        with contextlib.suppress(SystemExit):
            cli_perform_compile_goal(args.parent)
        _execute_after_compilation(args)


def _execute_after_compilation(args: RunArguments) -> NoReturn:
    """Run executable after compilation if user requested."""
    if args.parent.output_format != "executable":
        return cli_fatal_abort(
            text="Cannot execute after compilation due to output format is not set to an executable!",
        )

    host_target = infer_host_target()
    assert host_target
    host_compliance = (
        args.parent.target.architecture == host_target.architecture
        and args.parent.target.operating_system == host_target.operating_system
    )

    if not host_compliance:
        cli_fatal_abort(
            "Target differs from host target, cannot execute on current host without emulation layer, please execute on your own!\nFile was compiled, please remove execute flag!",
        )

    cli_message(
        "INFO",
        "Trying to execute compiled file due to execute flag...",
        verbose=args.parent.verbose,
    )

    with wrap_with_perf_time_taken("Execution", verbose=args.parent.verbose):
        try:
            process = execute_native_binary_executable(
                args.parent.output_filepath,
                args=[],
            )
            log_command(args.parent, process)
            exit_code = process.returncode
        except KeyboardInterrupt:
            if not args.parent.cli_debug_user_friendly_errors:
                raise
            cli_message("WARNING", "Execution was interrupted by user!")
            sys.exit(0)
        _log_child_exit_code(args.parent, exit_code)
        if args.propagate_execute_child_exit_code:
            sys.exit(exit_code)
    return sys.exit(0)


def _log_child_exit_code(args: BuildArguments, exit_code: int) -> None:
    if exit_code == 0:
        return cli_message(
            "INFO",
            f"Program finished with exit code {exit_code}!",
            verbose=args.verbose,
        )

    if is_segmentation_fault(exit_code):
        return cli_message(
            "ERROR",
            f"Program finished with segmentation fault exit code (SIGSEGV, {exit_code})!",
        )

    return cli_message(
        "ERROR",
        f"Program finished with fail exit code {exit_code}!",
        verbose=args.verbose,
    )
