"""Document symbols of a Gofra document."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gofra.lsp.features.lookup import collect_symbols

if TYPE_CHECKING:
    from gofra.lsp.documents import Document
    from libgofra.hir.module import Module


def document_symbols(module: Module, document: Document) -> list[dict[str, object]]:
    """Get the symbols that are declared in the given document."""
    return [symbol.to_document_symbol() for symbol in collect_symbols(module, document)]
