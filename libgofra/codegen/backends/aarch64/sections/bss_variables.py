"""AARCH64 uninitialized (BSS) data section emission."""

from __future__ import annotations

from typing import TYPE_CHECKING

from libgofra.codegen.common.uninitialized_data import (
    plan_uninitialized_data_symbols,
)
from libgofra.codegen.sections._factory import SectionType

if TYPE_CHECKING:
    from collections.abc import Mapping

    from libgofra.codegen.backends.aarch64.writer import WriterProtocol
    from libgofra.hir.variable import Variable
    from libgofra.types._base import Type


def write_uninitialized_data_section(
    writer: WriterProtocol,
    variables: Mapping[str, Variable[Type]],
) -> None:
    """Emit the BSS section for variables without initial values."""
    symbols = plan_uninitialized_data_symbols(variables)
    if not symbols:
        return

    writer.section(SectionType.BSS)
    aligned_by: int | None = None
    for symbol in symbols:
        if symbol.alignment != aligned_by:
            writer.directive("align", symbol.alignment)
            aligned_by = symbol.alignment

        writer.label(symbol.label)
        writer.sym_sect_directive("space", symbol.size)
