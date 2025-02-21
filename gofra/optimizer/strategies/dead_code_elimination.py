from collections.abc import Sequence

from gofra.parser.operators import Operator


def optimize_dead_code_elimination(
    unoptimized_operators: Sequence[Operator],
) -> Sequence[Operator]:
    """Remove dead code from final operators result."""
    return unoptimized_operators
