"""Lookup of the symbols that are declared in a document."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from gofra.lsp.positions import Position, position_to_index
from gofra.lsp.protocol import (
    SYMBOL_KIND_CLASS,
    SYMBOL_KIND_CONSTANT,
    SYMBOL_KIND_FUNCTION,
    SYMBOL_KIND_STRUCT,
    SYMBOL_KIND_TYPE_PARAMETER,
    SYMBOL_KIND_VARIABLE,
)
from libgofra.lexer.tokens import TokenLocation
from libgofra.types.composite.structure import StructureType
from libgofra.types.composite.union import UnionType
from libgofra.types.registry import get_default_propagated_type_registry

if TYPE_CHECKING:
    from collections.abc import Sequence

    from gofra.lsp.documents import Document
    from libgofra.hir.function import Function
    from libgofra.hir.module import Module
    from libgofra.hir.variable import Variable
    from libgofra.types._base import Type

#: Kinds of the symbols that can be found in a document.
KIND_FUNCTION: Final = "function"
KIND_PARAMETER: Final = "parameter"
KIND_VARIABLE: Final = "variable"
KIND_CONSTANT: Final = "constant"
KIND_STRUCT: Final = "struct"
KIND_UNION: Final = "union"
KIND_TYPE: Final = "type"

#: Matches a declaration of a structure, an union or a type alias.
DECLARATION_PATTERN: Final = re.compile(
    r"^\s*(?:pub\s+|extern\s+|inline\s+|packed\s+|reorder\s+)*"
    r"(struct|union|type)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)",
)

#: Characters that may be a part of an identifier.
IDENTIFIER_CHARACTERS: Final = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
)


@dataclass(frozen=True, slots=True)
class SymbolInfo:
    """Description of a symbol that is declared in a document."""

    name: str
    kind: str
    detail: str
    location: TokenLocation | None
    line: int = 0
    character: int = 0
    length: int = 0

    def to_document_symbol(self) -> dict[str, object]:
        """Convert the symbol into the protocol document symbol."""
        return {
            "name": self.name,
            "kind": _document_symbol_kind(self.kind),
            "detail": self.detail,
            "range": {
                "start": {"line": self.line, "character": self.character},
                "end": {"line": self.line, "character": self.character + self.length},
            },
            "selectionRange": {
                "start": {"line": self.line, "character": self.character},
                "end": {"line": self.line, "character": self.character + self.length},
            },
        }


def identifier_at(document: Document, position: Position) -> str | None:
    """Get the identifier that is placed under the given position."""
    lines = document.text.splitlines()
    if position.line < 0 or position.line >= len(lines):
        return None

    line = lines[position.line]
    index = position_to_index(position, lines)

    if index > 0 and line[index - 1] in IDENTIFIER_CHARACTERS:
        start = index - 1
        while start > 0 and line[start - 1] in IDENTIFIER_CHARACTERS:
            start -= 1
    elif index < len(line) and line[index] in IDENTIFIER_CHARACTERS:
        start = index
    else:
        return None

    end = start
    while end < len(line) and line[end] in IDENTIFIER_CHARACTERS:
        end += 1

    return line[start:end]


def collect_symbols(module: Module, document: Document) -> list[SymbolInfo]:
    """Collect all symbols that are declared in the given document."""
    symbols: list[SymbolInfo] = []

    for function in module.functions.values():
        if not _is_declared_in(function.defined_at, document):
            continue
        symbols.append(_function_symbol(function))

    for variable in module.variables.values():
        if not _is_declared_in(variable.defined_at, document):
            continue
        symbols.append(_variable_symbol(variable))

    symbols.extend(_declared_types(module, document))

    return symbols


def _is_declared_in(location: TokenLocation | None, document: Document) -> bool:
    """Check that the given location points into the given document."""
    if location is None or location.filepath is None:
        return False

    if location.filepath == document.path:
        return True

    return location.filepath.resolve() == document.path.resolve()


def find_symbol(
    symbols: Sequence[SymbolInfo],
    name: str,
) -> SymbolInfo | None:
    """Find a symbol with the given name."""
    for symbol in symbols:
        if symbol.name == name:
            return symbol

    return None


def find_enclosing_function(
    module: Module,
    document: Document,
    position: Position,
) -> Function | None:
    """Find the function that holds the given position."""
    best: Function | None = None
    best_line = -1

    for function in module.functions.values():
        if not function.operators:
            continue

        if not _is_declared_in(function.defined_at, document):
            continue

        first_line = min(
            function.defined_at.line_number,
            function.operators[0].location.line_number,
        )
        last_line = function.operators[-1].location.line_number

        if first_line <= position.line <= last_line and first_line > best_line:
            best = function
            best_line = first_line

    return best


def _function_symbol(function: Function) -> SymbolInfo:
    """Build a symbol out of a function definition."""
    parameters = ", ".join(repr(parameter) for parameter in function.parameters)
    detail = f"{function.return_type} {function.name}({parameters})"

    return _make_symbol(
        name=function.name,
        kind=KIND_FUNCTION,
        detail=detail,
        location=function.defined_at,
    )


def _variable_symbol(variable: Variable[Type]) -> SymbolInfo:
    """Build a symbol out of a variable definition."""
    kind = KIND_CONSTANT if variable.is_constant else KIND_VARIABLE
    detail = f"{variable.type} {variable.name}"

    return _make_symbol(
        name=variable.name,
        kind=kind,
        detail=detail,
        location=variable.defined_at,
    )


def _declared_types(module: Module, document: Document) -> list[SymbolInfo]:
    """Build symbols out of the structures, unions and type aliases."""
    primitive_names = set(get_default_propagated_type_registry())

    symbols: list[SymbolInfo] = []
    for name, type_ in module.types.items():
        if name in primitive_names:
            continue

        if isinstance(type_, StructureType):
            kind = KIND_STRUCT
            detail = f"struct {name}"
        elif isinstance(type_, UnionType):
            kind = KIND_UNION
            detail = f"union {name}"
        else:
            kind = KIND_TYPE
            detail = f"type {name}"

        location = _find_declaration_location(name, document)
        symbols.append(
            _make_symbol(
                name=name,
                kind=kind,
                detail=detail,
                location=location,
            ),
        )

    return symbols


def _find_declaration_location(
    name: str,
    document: Document,
) -> TokenLocation | None:
    """Find the source location of a declaration with the given name."""
    lines = document.text.splitlines()

    for index, line in enumerate(lines):
        match = DECLARATION_PATTERN.match(line)
        if match is None or match.group("name") != name:
            continue

        column = line.index(name, match.start())
        return _fake_location(
            document=document,
            line_number=index,
            col_number=column,
        )

    return None


def _make_symbol(
    *,
    name: str,
    kind: str,
    detail: str,
    location: TokenLocation | None,
) -> SymbolInfo:
    """Build a symbol with all the information needed by the protocol."""
    line = 0
    character = 0

    if location is not None:
        line = max(location.line_number, 0)
        character = max(location.col_number, 0)

    return SymbolInfo(
        name=name,
        kind=kind,
        detail=detail,
        location=location,
        line=line,
        character=character,
        length=len(name),
    )


def _fake_location(
    *,
    document: Document,
    line_number: int,
    col_number: int,
) -> TokenLocation:
    """Build a source location for a place that is found in the document text."""
    return TokenLocation(
        filepath=document.path,
        line_number=line_number,
        col_number=col_number,
    )


def _document_symbol_kind(kind: str) -> int:
    """Get the protocol symbol kind of the given symbol kind."""
    return {
        KIND_FUNCTION: SYMBOL_KIND_FUNCTION,
        KIND_PARAMETER: SYMBOL_KIND_VARIABLE,
        KIND_VARIABLE: SYMBOL_KIND_VARIABLE,
        KIND_CONSTANT: SYMBOL_KIND_CONSTANT,
        KIND_STRUCT: SYMBOL_KIND_STRUCT,
        KIND_UNION: SYMBOL_KIND_CLASS,
        KIND_TYPE: SYMBOL_KIND_TYPE_PARAMETER,
    }.get(kind, SYMBOL_KIND_VARIABLE)
