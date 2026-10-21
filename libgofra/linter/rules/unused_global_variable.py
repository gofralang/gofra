from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from libgofra.linter.diagnostics import LintDiagnostic, LintLevel

if TYPE_CHECKING:
    from collections.abc import Iterable

    from libgofra.hir.module import Module
    from libgofra.hir.variable import Variable
    from libgofra.linter.context import LintContext


@dataclass(frozen=True, slots=True)
class UnusedGlobalVariableRule:
    id = "unused-global-variable"
    description = (
        "Global variable is declared but never read or written. "
        "Either use it, prefix with `_`, or remove it."
    )
    level = LintLevel.WARN

    def check(self, module: Module, context: LintContext) -> Iterable[LintDiagnostic]:
        for variable in self._iter_candidate_variables(module):
            if context.references.is_global_used(variable.name):
                continue
            if variable.name.startswith("_"):
                continue
            yield LintDiagnostic(
                rule_id=self.id,
                level=self.level,
                message=(
                    f"Unused non-constant global variable `{variable.name}` "
                    f"defined at {variable.defined_at}."
                ),
                at=variable.defined_at,
            )

    def _iter_candidate_variables(self, module: Module) -> Iterable[Variable]:
        for variable in module.variables.values():
            if variable.is_constant:
                continue
            yield variable
