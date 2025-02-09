from typing import Callable

from gofra.parser import Operator

from .strategies import optimize_constant_folding

type FoldPredicate = Callable[[int, int], int]


def optimize_operators(unoptimized_operators: list[Operator]) -> list[Operator]:
    operators = optimize_constant_folding(unoptimized_operators)
    return operators
