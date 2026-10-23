"""Hover information of a Gofra document."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from gofra.lsp.features.lookup import (
    SymbolInfo,
    collect_symbols,
    find_enclosing_function,
    find_symbol,
    identifier_at,
)

if TYPE_CHECKING:
    from gofra.lsp.documents import Document
    from gofra.lsp.positions import Position
    from libgofra.hir.function import Function
    from libgofra.hir.module import Module
    from libgofra.hir.operator import Operator
    from libgofra.types._base import Type

#: Kind of the markup content that is used to show the hover information.
MARKUP_KIND_MARKDOWN: Final = "markdown"


def hover(
    module: Module,
    document: Document,
    position: Position,
) -> dict[str, object] | None:
    """Get the hover information for the place under the given position."""
    name = identifier_at(document, position)
    if name is None:
        return None

    function = find_enclosing_function(module, document, position)

    symbol = _find_local_symbol(function, name)
    if symbol is None:
        symbol = find_symbol(collect_symbols(module, document), name)

    if symbol is not None:
        return _hover_content(symbol.detail, symbol.kind)

    expression_type = _expression_type(function, name, position.line)
    if expression_type is not None:
        return _hover_content(f"{expression_type} (expression)", "variable")

    return None


def _find_local_symbol(
    function: Function | None,
    name: str,
) -> SymbolInfo | None:
    """Find a local variable or a parameter with the given name."""
    if function is None:
        return None

    variable = function.variables.get(name)
    if variable is not None:
        return SymbolInfo(
            name=name,
            kind="variable",
            detail=f"{variable.type} {name}",
            location=variable.defined_at,
        )

    parameter = function.parameter_map.get(name)
    if parameter is not None:
        return SymbolInfo(
            name=name,
            kind="parameter",
            detail=f"{parameter.type} {name}",
            location=None,
        )

    return None


def _expression_type(
    function: Function | None,
    name: str,
    line: int,
) -> Type | None:
    """Get the type of the value that is produced by the given expression."""
    operator = _find_operator(function, name, line)
    if operator is None:
        return None

    meta = operator.tc_meta
    if meta is None or isinstance(meta, str):
        return None

    return meta


def _find_operator(
    function: Function | None,
    name: str,
    line: int,
) -> Operator | None:
    """Find the operator that is produced by the given identifier."""
    if function is None:
        return None

    for operator in function.operators:
        token = operator.token
        if token.text != name:
            continue
        if token.location.line_number != line:
            continue
        return operator

    return None


def _hover_content(detail: str, kind: str) -> dict[str, object]:
    """Build the hover content out of the given symbol details."""
    del kind

    return {
        "contents": {
            "kind": MARKUP_KIND_MARKDOWN,
            "value": f"```gofra\n{detail}\n```",
        },
    }
