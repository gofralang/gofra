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
class UnusedLocalVariableRule:
    id = "unused-local-variable"
    description = (
        "Function local variable is declared but never used in the function body. "
        "Either use it, prefix with `_`, or remove it."
    )
    level = LintLevel.WARN

    def check(self, module: Module, context: LintContext) -> Iterable[LintDiagnostic]:
        for function in module.executable_functions:
            yield from self._check_function(function, context)

    def _check_function(
        self,
        function: Function,
        context: LintContext,
    ) -> Iterable[LintDiagnostic]:
        # Parameters are materialized as local variables of the function scope,
        # so they are excluded here -- unused parameters are reported by
        # the `unused-parameter` rule instead.
        parameter_names = set(function.parameter_map.keys())

        for name, variable in function.variables.items():
            if name in parameter_names:
                continue
            if context.references.is_local_used(function.name, name):
                continue
            if name.startswith("_"):
                continue

            yield LintDiagnostic(
                rule_id=self.id,
                level=self.level,
                message=(
                    f"Unused function variable '{name}' declared at "
                    f"{variable.defined_at}, either remove it or use it"
                ),
                at=variable.defined_at,
            )
