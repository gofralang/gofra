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
class UnusedParameterRule:
    id = "unused-parameter"
    description = (
        "Function parameter is declared but never used in the function body. "
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
        if function.attrs.naked:
            # Naked function body is a raw assembly, so its parameters are read
            # directly from the registers (per C ABI) and cannot be tracked here
            return

        for param in function.parameters:
            if context.references.is_local_used(function.name, param.name):
                continue
            if param.name.startswith("_"):
                continue
            yield LintDiagnostic(
                rule_id=self.id,
                level=self.level,
                message=(
                    f"Unused parameter `{param.name}` in function "
                    f"`{function.name}` defined at {function.defined_at}."
                ),
                at=function.defined_at,
            )
