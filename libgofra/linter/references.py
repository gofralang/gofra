from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from libgofra.hir.operator import OperatorType

if TYPE_CHECKING:
    from libgofra.hir.module import Module


@dataclass(frozen=True, slots=True)
class References:
    """Which variable names are referenced, grouped by scope.

    Global names are module-wide. Local names are per-function, so that
    same-name locals in different functions do not mask each other.
    """

    global_refs: frozenset[str] = field(default_factory=frozenset)
    local_refs: dict[str, frozenset[str]] = field(default_factory=dict)
    # key: function name, value: set of names referenced inside that function

    def is_global_used(self, name: str) -> bool:
        return name in self.global_refs

    def is_local_used(self, function_name: str, name: str) -> bool:
        return name in self.local_refs.get(function_name, frozenset())


def collect_references(module: Module) -> References:
    global_refs: set[str] = set()
    local_refs: dict[str, set[str]] = {}

    for function in module.executable_functions:
        used: set[str] = set()
        for op in function.operators:
            if op.type in (
                OperatorType.PUSH_VARIABLE_ADDRESS,
                OperatorType.PUSH_VARIABLE_VALUE,
            ):
                assert isinstance(op.operand, str)
                used.add(op.operand)
        local_refs[function.name] = used

    # A name is "global" if it appears in module.variables
    # and is referenced anywhere. A name only appearing in functions
    # is local (or parameter) and handled per-function.
    global_names = set(module.variables.keys())
    for used in local_refs.values():
        global_refs |= used & global_names

    return References(
        global_refs=frozenset(global_refs),
        local_refs={k: frozenset(v) for k, v in local_refs.items()},
    )
