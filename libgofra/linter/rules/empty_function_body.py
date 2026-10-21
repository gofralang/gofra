from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from libgofra.linter.diagnostics import LintDiagnostic, LintLevel

if TYPE_CHECKING:
    from collections.abc import Iterable

    from libgofra.hir.function import Function
    from libgofra.hir.module import Module
    from libgofra.linter.context import LintContext


@dataclass(frozen=True, slots=True)
class EmptyFunctionBodyRule:
    id = "empty-function-body"
    description = (
        "Function has no executable body (no operators). "
        "Either implement it, mark it as `extern`, or remove it."
    )
    level = LintLevel.WARN

    def check(self, module: Module, context: LintContext) -> Iterable[LintDiagnostic]:  # noqa: ARG002
        for function in self._iter_candidate_functions(module):
            yield LintDiagnostic(
                rule_id=self.id,
                level=self.level,
                message=(
                    f"Function `{function.name}` defined at {function.defined_at} "
                    f"has no executable body!"
                ),
                at=function.defined_at,
            )

    def _iter_candidate_functions(self, module: Module) -> Iterable[Function]:
        for function in module.executable_functions:
            if function.operators:
                continue
            yield function
