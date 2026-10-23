"""Tests of the analysis of a Gofra document."""

from pathlib import Path

from gofra.lsp.analysis import analyze_document
from gofra.lsp.documents import Document

VALID_SOURCE = """pub func int add[int a, int b]
    a b +
end
"""

UNUSED_VARIABLE_SOURCE = """#include "std"

pub func void main[]
    var counter int = 0
    1 exit
end
"""

BROKEN_SOURCE = """pub func void main[
    1 exit
end
"""


def _document(source: str, tmp_path: Path) -> Document:
    """Build a document out of the given source."""
    path = tmp_path / "gofra-lsp-test.gof"
    return Document(
        uri=path.as_uri(),
        path=path,
        text=source,
        version=1,
    )


def test_valid_document_has_no_diagnostics(tmp_path: Path) -> None:
    analysis = analyze_document(_document(VALID_SOURCE, tmp_path))

    assert analysis.diagnostics == ()
    assert analysis.module is not None


def test_unused_variable_is_reported(tmp_path: Path) -> None:
    analysis = analyze_document(_document(UNUSED_VARIABLE_SOURCE, tmp_path))

    codes = [diagnostic.code for diagnostic in analysis.diagnostics]
    assert "unused-local-variable" in codes


def test_syntax_error_is_reported(tmp_path: Path) -> None:
    analysis = analyze_document(_document(BROKEN_SOURCE, tmp_path))

    assert analysis.diagnostics
    assert analysis.diagnostics[0].severity == 1


def test_diagnostic_points_at_the_source_of_the_problem(tmp_path: Path) -> None:
    analysis = analyze_document(_document(UNUSED_VARIABLE_SOURCE, tmp_path))

    diagnostic = next(
        diagnostic
        for diagnostic in analysis.diagnostics
        if diagnostic.code == "unused-local-variable"
    )

    assert diagnostic.range.start.line == 3
    assert diagnostic.range.start.character == 8
