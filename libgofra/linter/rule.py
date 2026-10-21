from collections.abc import Iterable
from typing import Protocol

from libgofra.hir.module import Module
from libgofra.linter.context import LintContext
from libgofra.linter.diagnostics import LintDiagnostic, LintLevel


class LintRule(Protocol):
    id: str

    level: LintLevel

    def check(
        self,
        module: Module,
        context: LintContext,
    ) -> Iterable[LintDiagnostic]: ...
