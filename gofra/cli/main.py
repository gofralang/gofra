from __future__ import annotations

from sys import argv

from gofra.cli.commands import clean, version
from gofra.cli.commands.build import command as build
from gofra.cli.parser.builder import build_cli_parser
from gofra.executable import cli_get_executable_program, warn_on_improper_installation

from .output import cli_fatal_abort


def cli_entry_point() -> None:
    """CLI main entry."""
    prog = cli_get_executable_program()
    warn_on_improper_installation(prog)

    parser = build_cli_parser(prog)
    raw_args = parser.parse_args()

    match raw_args.command:
        case "version":
            version.execute(version.parse_arguments(raw_args))
        case "clean":
            clean.execute(clean.parse_arguments(raw_args))
        case "build":
            build.execute(build.parse_arguments(raw_args))
        case _:
            cli_fatal_abort(f"Unknown command: {raw_args.command}")


def cli_compiler_entry_point() -> None:
    # Backward compatibility
    argv.insert(1, "build")
    cli_entry_point()


if __name__ == "__main__":
    cli_entry_point()
