import sys
from subprocess import CalledProcessError, run

from gofra.assembler import assemble_executable
from gofra.gofra import parse_and_tokenize_input_file
from gofra.parser import Operator

from .arguments import CLIArguments, parse_cli_arguments
from .errors import cli_user_error_handler
from .output import cli_message


def cli_entry_point() -> None:
    with cli_user_error_handler():
        args = parse_cli_arguments()
        operators = parse_and_tokenize_input_file(args.filepath)

        if args.action_compile:
            _cli_compile_action(operators, args)


def _cli_compile_action(operators: list[Operator], args: CLIArguments) -> None:
    cli_message("INFO", "Trying to compile input file...")

    assemble_executable(
        operators=operators,
        output=args.filepath_output,
        architecture=args.target_architecture,
        os=args.target_os,
        build_cache_delete_after_end=args.build_cache_delete_after_run,
        build_cache_directory=args.build_cache_directory,
    )

    cli_message(
        "INFO", f"Compiled input file down to executable `{args.filepath_output.name}`!"
    )

    if args.execute_after_compile:
        _cli_execute_after_compilation(args)


def _cli_execute_after_compilation(args: CLIArguments):
    cli_message("INFO", "Trying to execute compiled file due to execute flag...")
    exit_code = 0
    try:
        run(
            [args.filepath_output.absolute()],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )
    except CalledProcessError as e:
        exit_code = e.returncode

    level = "INFO" if exit_code == 0 else "ERROR"
    cli_message(level, f"Program finished with exit code {exit_code}!")
