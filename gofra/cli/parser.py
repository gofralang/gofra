from argparse import ArgumentParser

from gofra.cli.commands import clean, run, version
from gofra.cli.commands.build import command as build


def build_root_cli_parser(prog: str) -> ArgumentParser:
    """Get argument parser instance to parse incoming arguments."""
    core_parser = ArgumentParser(
        description="Gofra Toolkit - CLI for working with Gofra programming language",
        add_help=True,
        allow_abbrev=False,
        prog=prog,
    )

    subparsers = core_parser.add_subparsers(
        dest="command",
        title="Commands",
        description="Available commands",
        help="Command to execute",
        required=True,
    )

    version.build_parser(subparsers)
    run.build_parser(subparsers)

    clean.build_parser(subparsers)
    build.build_parser(subparsers)

    return core_parser
