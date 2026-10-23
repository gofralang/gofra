"""Completion support of a Gofra document."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from gofra.lsp.features.lookup import (
    collect_symbols,
    find_enclosing_function,
)
from gofra.lsp.protocol import (
    COMPLETION_KIND_CLASS,
    COMPLETION_KIND_CONSTANT,
    COMPLETION_KIND_FUNCTION,
    COMPLETION_KIND_KEYWORD,
    COMPLETION_KIND_STRUCT,
    COMPLETION_KIND_VARIABLE,
)
from libgofra.lexer.keywords import WORD_TO_KEYWORD

if TYPE_CHECKING:
    from gofra.lsp.documents import Document
    from gofra.lsp.positions import Position
    from libgofra.hir.module import Module

#: Kind of the completion that is used for the language keywords.
KEYWORDS_KIND: Final = COMPLETION_KIND_KEYWORD


def completion(
    module: Module,
    document: Document,
    position: Position,
) -> list[dict[str, object]]:
    """Get the completion items that are available at the given position."""
    items: list[dict[str, object]] = [
        _item(keyword, KEYWORDS_KIND, "keyword")
        for keyword in sorted(WORD_TO_KEYWORD)
        if not keyword.startswith("#")
    ]

    items.extend(
        _item(symbol.name, _completion_kind(symbol.kind), symbol.detail)
        for symbol in collect_symbols(module, document)
    )

    function = find_enclosing_function(module, document, position)
    if function is not None:
        items.extend(
            _item(name, COMPLETION_KIND_VARIABLE, f"{variable.type} {name}")
            for name, variable in function.variables.items()
        )

    return items


def _item(label: str, kind: int, detail: str) -> dict[str, object]:
    """Build a completion item."""
    return {
        "label": label,
        "kind": kind,
        "detail": detail,
    }


def _completion_kind(kind: str) -> int:
    """Get the protocol completion kind of the given symbol kind."""
    match kind:
        case "function":
            return COMPLETION_KIND_FUNCTION
        case "constant":
            return COMPLETION_KIND_CONSTANT
        case "struct":
            return COMPLETION_KIND_STRUCT
        case "union":
            return COMPLETION_KIND_CLASS
        case "type":
            return COMPLETION_KIND_CLASS
        case _:
            return COMPLETION_KIND_VARIABLE
