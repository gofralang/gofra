"""Backend-agnostic planning for uninitialized (BSS) data symbols.

This module owns *what* needs to be emitted (symbol, size, alignment), but not the
assembler syntax. Backends keep responsibility for emitting directives and storing
the chosen layout into the concrete assembly text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from libgofra.codegen.common.mangling import mangle_hir_symbol_name

if TYPE_CHECKING:
    from collections.abc import Mapping

    from libgofra.hir.variable import Variable
    from libgofra.types._base import Type


@dataclass(frozen=True, slots=True)
class UninitializedDataSymbol:
    """One symbol to be allocated in an uninitialized data section."""

    label: str
    size: int
    alignment: int


def plan_uninitialized_data_symbols(
    variables: Mapping[str, Variable[Type]],
) -> list[UninitializedDataSymbol]:
    """Build a deterministic plan of uninitialized variable symbols.

    The input mapping is not assumed to be ordered; callers emit using the order
    returned here. Only variable metadata is considered.
    """
    result: list[UninitializedDataSymbol] = []
    for variable in variables.values():
        if variable.initial_value is not None:
            continue

        size = variable.size_in_bytes
        assert size > 0, (
            f"Variable has type with zero size ({variable.name} defined at "
            f"{variable.defined_at})"
        )
        assert variable.type.alignment > 0, (
            f"Variable type alignment is not positive ({variable.name})"
        )
        assert (variable.type.alignment & (variable.type.alignment - 1)) == 0, (
            f"Variable type alignment is not a power of two ({variable.name})"
        )

        result.append(
            UninitializedDataSymbol(
                label=mangle_hir_symbol_name(variable),
                size=size,
                alignment=variable.type.alignment,
            ),
        )
    return result
