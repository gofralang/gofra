"""Optimization strategies applied to the program to optimize it."""

from .constant_folding import optimize_constant_folding
from .dead_code_elimination import optimize_dead_code_elimination

__all__ = ["optimize_constant_folding", "optimize_dead_code_elimination"]
