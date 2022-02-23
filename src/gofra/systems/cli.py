"""
    'Gofra' CLI module.
    Contains all stuff releated to the CLI part.
"""

from typing import Optional
from sys import stdout
from os.path import basename


# Constants.
__PREFIX = "[Gofra CLI]"


def welcome_message():
    """
     Shows CLI welcome message.
    """

    print(f"{__PREFIX} Welcome to the Gofra CLI!", file=stdout)


def usage_message(runner_filename: Optional[str] = None):
    """
    Shows CLI usage message.
    :param: runner_filename Should be '__file__'.
    """
    if runner_filename is None:
        runner_filename = __file__
    assert isinstance(runner_filename, str), "Fatal error! CLI Usage message got non-string runner filename!"
    runner_filename = basename(runner_filename)

    print(f"{__PREFIX} Usage: {runner_filename} [source] [subcommand]\n"
          f"Subcommands:\n"
          f"\thelp; This message.\n"
          f"\trun; Interpretates source.\n"
          f"\tpython; Compiles source file to python source file\n"
          f"\tcompile; Compiles source file to bytecode file\n"
          f"\texecute; Executes source file from bytecode [*.gofbc] (NOTE: use `compile` command)\n"
          f"\tdump; Dumps operators from the source\n"
          f"\tgraph; Generates graphviz file from the source", file=stdout)
