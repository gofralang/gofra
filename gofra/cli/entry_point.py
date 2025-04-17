import sys
from subprocess import CalledProcessError, run

from gofra.assembler import assemble_executable
from gofra.context import ProgramContext
from gofra.gofra import process_input_file

from .arguments import CLIArguments, parse_cli_arguments
from .errors import cli_user_error_handler
from .output import cli_message


def cli_entry_point() -> None:
    with cli_user_error_handler():
        args = parse_cli_arguments()
        context = process_input_file(
            args.filepath,
            optimize=not args.no_optimizations,
            typecheck=not args.no_typecheck,
            include_search_directories=args.include_search_directories,
        )
        if args.action_compile:
            _cli_compile_action(context, args)


def _cli_compile_action(context: ProgramContext, args: CLIArguments) -> None:
    cli_message("INFO", "Trying to compile input file...")

    assemble_executable(
        context=context,
        output=args.filepath_output,
        architecture=args.target_architecture,
        os=args.target_os,
        build_cache_delete_after_end=args.build_cache_delete_after_run,
        build_cache_directory=args.build_cache_directory,
    )

    cli_message(
        "INFO",
        f"Compiled input file down to executable `{args.filepath_output.name}`!",
    )

    if args.fall_into_debugger:
        _cli_fall_into_debugger_after_compilation(args)
    elif args.execute_after_compile:
        _cli_execute_after_compilation(args)


def _cli_execute_after_compilation(args: CLIArguments) -> None:
    cli_message("INFO", "Trying to execute compiled file due to execute flag...")
    exit_code = 0
    try:
        run(  # noqa: S602
            [args.filepath_output.absolute()],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
            shell=True,
        )
    except CalledProcessError as e:
        exit_code = e.returncode
    except KeyboardInterrupt:
        cli_message("INFO", "Execution was interrupted by user!")
        sys.exit(0)

    level = "INFO" if exit_code == 0 else "ERROR"
    cli_message(level, f"Program finished with exit code {exit_code}!")


def _cli_fall_into_debugger_after_compilation(args: CLIArguments) -> None:
    cli_message(
        "INFO",
        "Trying to fall into debugger for compiled file due to debugger flag...",
    )

    compiled_target_path = args.filepath_output.absolute()

    cmd_args = ["-o", "run"]

    exit_code = 0
    try:
        run(  # noqa: S603
            ["/usr/bin/lldb", str(compiled_target_path), *cmd_args],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True,
        )
    except CalledProcessError as e:
        exit_code = e.returncode
    except KeyboardInterrupt:
        cli_message("INFO", "Debugger was interrupted by user!")
        sys.exit(0)

    level = "INFO" if exit_code == 0 else "ERROR"
    cli_message(level, f"Debugger finished with exit code {exit_code}!")
