"""Go to definition support of a Gofra document."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gofra.lsp.features.lookup import (
    collect_symbols,
    find_enclosing_function,
    find_symbol,
    identifier_at,
)
from gofra.lsp.positions import location_to_range

if TYPE_CHECKING:
    from gofra.lsp.documents import Document
    from gofra.lsp.positions import Position
    from libgofra.hir.module import Module


def definition(
    module: Module,
    document: Document,
    position: Position,
) -> list[dict[str, object]] | None:
    """Get the location of the definition of the symbol under the given position."""
    name = identifier_at(document, position)
    if name is None:
        return None

    location = _definition_location(module, document, name, position)
    if location is None:
        return None

    return [
        {
            "uri": document.uri,
            "range": location_to_range(location, document.lines).to_lsp(),
        },
    ]


def _definition_location(
    module: Module,
    document: Document,
    name: str,
    position: Position,
) -> object | None:
    """Find the source location of the definition of the given name."""
    function = find_enclosing_function(module, document, position)
    if function is not None:
        variable = function.variables.get(name)
        if variable is not None:
            return variable.defined_at

    symbol = find_symbol(collect_symbols(module, document), name)
    if symbol is None:
        return None

    return symbol.location
