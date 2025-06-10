from gofra.context import ProgramContext

from .strategies import (
    optimize_constant_folding,
    optimize_dead_code_elimination,
)


def optimize_program(program: ProgramContext) -> None:
    """Apply optimization strategies within given program context."""
    optimize_constant_folding(program)
    optimize_dead_code_elimination(program)
