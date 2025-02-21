from collections.abc import Sequence

from gofra.parser import Operator

from .strategies import (
    optimize_constant_folding,
    optimize_dead_code_elimination,
)


def optimize_operators(unoptimized_operators: Sequence[Operator]) -> Sequence[Operator]:
    """Apply optimization strategies within given operators."""
    operators = optimize_constant_folding(unoptimized_operators)
    operators = optimize_dead_code_elimination(operators)

    return operators  # noqa: RET504
