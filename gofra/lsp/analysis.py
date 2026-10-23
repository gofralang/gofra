"""Bridge between the language server and the Gofra compiler.

The compiler is a batch oriented toolchain, so the analysis of a document is
performed by running the frontend, the type checker and the linter over the
document content, and by collecting everything they report.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from gofra.lsp.positions import Position, Range, location_to_range
from gofra.lsp.protocol import SEVERITY_ERROR, SEVERITY_WARNING
from libgofra.driver.stages.frontend import load_module_graph
from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation
from libgofra.linter.config import LintConfig
from libgofra.linter.diagnostics import LintDiagnostic, LintLevel
from libgofra.linter.registry import get_default_registry
from libgofra.linter.runner import LintRunner
from libgofra.preprocessor.include.distribution import infer_distribution_library_paths
from libgofra.preprocessor.macros.registry import (
    MacrosRegistry,
    registry_from_raw_definitions,
)
from libgofra.targets.infer_host import infer_host_target
from libgofra.typecheck import validate_type_safety

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from gofra.lsp.documents import Document
    from libgofra.hir.module import Module

#: Name of the entry point that is expected in a compiled program.
ENTRY_POINT_NAME: Final = "main"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """A problem that was found in a document."""

    message: str
    range: Range
    severity: int
    code: str

    def to_lsp(self) -> dict[str, object]:
        """Convert the diagnostic into the protocol representation."""
        return {
            "range": self.range.to_lsp(),
            "severity": self.severity,
            "code": self.code,
            "source": "gofra",
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class Analysis:
    """Result of the analysis of a single document."""

    module: Module | None
    diagnostics: tuple[Diagnostic, ...]


def analyze_document(document: Document) -> Analysis:
    """Analyze the given document and collect all found problems."""
    lines = document.text.splitlines(keepends=True)

    try:
        module = load_module_graph(
            document.path,
            _include_paths(document),
            macros=_macros(),
            source_lines=lines,
        )
    except GofraError as error:
        return Analysis(
            module=None,
            diagnostics=(diagnostic_from_error(error, lines),),
        )

    diagnostics: list[Diagnostic] = []

    diagnostics.extend(_lint_diagnostics(module, lines))
    diagnostics.extend(_typecheck_diagnostics(module, lines))

    return Analysis(module=module, diagnostics=tuple(diagnostics))


def diagnostic_from_error(
    error: GofraError,
    lines: Sequence[str],
) -> Diagnostic:
    """Build a diagnostic out of a compiler error."""
    location = _error_location(error)
    message = _error_message(error)
    code = _error_code(error)

    if location is None:
        return Diagnostic(
            message=message,
            range=Range(start=_zero_position(), end=_zero_position()),
            severity=SEVERITY_ERROR,
            code=code,
        )

    return Diagnostic(
        message=message,
        range=location_to_range(location, lines),
        severity=SEVERITY_ERROR,
        code=code,
    )


def _lint_diagnostics(
    module: Module,
    lines: Sequence[str],
) -> list[Diagnostic]:
    """Collect the diagnostics produced by the linter."""
    runner = LintRunner(
        registry=get_default_registry(),
        config=LintConfig(),
    )

    return [
        _lint_diagnostic_to_diagnostic(lint_diagnostic, lines)
        for lint_diagnostic in runner.check(module)
    ]


def _lint_diagnostic_to_diagnostic(
    lint_diagnostic: LintDiagnostic,
    lines: Sequence[str],
) -> Diagnostic:
    """Convert a linter diagnostic into a protocol diagnostic."""
    severity = SEVERITY_ERROR
    if lint_diagnostic.level == LintLevel.WARN:
        severity = SEVERITY_WARNING

    location = lint_diagnostic.at
    if location is None:
        location_range = Range(start=_zero_position(), end=_zero_position())
    else:
        location_range = location_to_range(location, lines)

    return Diagnostic(
        message=lint_diagnostic.message,
        range=location_range,
        severity=severity,
        code=lint_diagnostic.rule_id,
    )


def _typecheck_diagnostics(
    module: Module,
    lines: Sequence[str],
) -> list[Diagnostic]:
    """Collect the diagnostics produced by the type checker."""
    try:
        validate_type_safety(
            module,
            strict_expect_entry_point=False,
            on_lint_warning=None,
            entry_point_name=ENTRY_POINT_NAME,
        )
    except GofraError as error:
        return [diagnostic_from_error(error, lines)]

    return []


def _include_paths(document: Document) -> list[Path]:
    """Get the include paths that are used to resolve the includes of a document."""
    paths: list[Path] = []

    parent = document.path.parent
    if str(parent):
        paths.append(parent)

    paths.extend(infer_distribution_library_paths())
    return paths


def _macros() -> MacrosRegistry:
    """Build the macros registry that is used during the analysis."""
    target = infer_host_target()
    return registry_from_raw_definitions(
        location=TokenLocation.cli(),
        definitions={},
    ).inject_propagated_defaults(target=target)


def _error_location(error: GofraError) -> TokenLocation | None:
    """Get the source location that is reported by a compiler error."""
    at = getattr(error, "at", None)
    if isinstance(at, TokenLocation):
        return at

    got = getattr(error, "got", None)
    location = getattr(got, "location", None)
    if isinstance(location, TokenLocation):
        return location

    location = getattr(error, "location", None)
    if isinstance(location, TokenLocation):
        return location

    return None


def _error_message(error: GofraError) -> str:
    """Get a human readable message of a compiler error."""
    lines = [line.strip() for line in repr(error).splitlines() if line.strip()]
    if not lines:
        return type(error).__name__

    return lines[0]


def _error_code(error: GofraError) -> str:
    """Get a stable machine readable code of a compiler error."""
    return error.generic_error_name.strip("[]")


def _zero_position() -> Position:
    """Get the position of the very beginning of a document."""
    return Position(line=0, character=0)
