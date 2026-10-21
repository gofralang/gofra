from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from libgofra.linter.diagnostics import LintDiagnostic, LintLevel

if TYPE_CHECKING:
    from collections.abc import Iterable

    from libgofra.hir.module import Module
    from libgofra.linter.context import LintContext


@dataclass(frozen=True, slots=True)
class UnusedPrivateFunctionRule:
    id = "unused-private-function"
    description = (
        "Private function is never called from anywhere in the module. "
        "Either remove it or make it public."
    )
    level = LintLevel.WARN

    def check(self, module: Module, context: LintContext) -> Iterable[LintDiagnostic]:  # noqa: ARG002
        call_graph = context.call_graph
        if call_graph is None:
            return

        for function in call_graph.get_root_functions():
            if function.is_public:
                continue
            if function.attrs.external:
                continue
            if function.attrs.inline:
                # Inline ones are always internal private but probably track usages?
                continue

            yield LintDiagnostic(
                rule_id=self.id,
                level=self.level,
                message=(
                    f"Unused private module function {function.name} "
                    f"defined at {function.defined_at}! "
                    f"Either remove it or make public!"
                ),
                at=function.defined_at,
            )
