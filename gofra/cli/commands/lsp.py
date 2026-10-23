"""The `gofra lsp` command - runs the Gofra language server."""

import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from dataclasses import dataclass
from typing import NoReturn

from gofra.lsp.server import serve


@dataclass(slots=True, frozen=True)
class LspArguments:
    """Arguments of the `lsp` command."""


def parse_arguments(namespace: Namespace) -> LspArguments:  # noqa: ARG001
    """Parse the arguments of the `lsp` command."""
    return LspArguments()


def build_parser(subparsers: "_SubParsersAction[ArgumentParser]") -> ArgumentParser:
    """Build the parser of the `lsp` command."""
    parser = subparsers.add_parser(
        "lsp",
        help="Run the Gofra language server",
        description="Run the Gofra language server (LSP) that serves language features to editors",
        allow_abbrev=False,
    )

    return parser  # noqa: RET504


def execute(args: LspArguments) -> NoReturn:
    """Run the language server until the client closes the connection."""
    _ = args

    exit_code = serve()
    return sys.exit(exit_code)
