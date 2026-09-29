"""Goals for CLI (e.g compile, show version) as different goals that output different result."""

import sys
from time import perf_counter_ns
from typing import NoReturn

from gofra.cli.commands.build.arguments import BuildArguments
from gofra.cli.output import cli_message

from .call_graph_visualizer import cli_perform_call_graph_goal
from .compile import cli_perform_compile_goal
from .hir import cli_perform_hir_goal
from .preprocessor import cli_perform_preprocess_goal

NANOS_TO_SECONDS = 1_000_000_000


def perform_desired_toolchain_goal(args: BuildArguments) -> NoReturn:
    """Perform toolchain goal base on CLI arguments, by default fall into compile goal."""
    start = perf_counter_ns()
    try:
        if args.preprocess_only:
            return cli_perform_preprocess_goal(args)

        if args.hir:
            return cli_perform_hir_goal(args)

        if args.call_graph_only:
            return cli_perform_call_graph_goal(args)

        return cli_perform_compile_goal(args)
    except SystemExit as e:
        end = perf_counter_ns()
        time_taken = (end - start) / NANOS_TO_SECONDS
        cli_message(
            "INFO",
            f"Performing an goal took {time_taken:.2f} seconds!",
            verbose=args.verbose,
        )
        sys.exit(e.code)
