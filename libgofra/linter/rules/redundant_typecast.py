from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from libgofra.hir.operator import OperatorType, TypecastMeta
from libgofra.linter.diagnostics import LintDiagnostic, LintLevel
from libgofra.types.comparison import is_types_same

if TYPE_CHECKING:
    from collections.abc import Iterable

    from libgofra.hir.function import Function
    from libgofra.hir.module import Module
    from libgofra.linter.context import LintContext


@dataclass(frozen=True, slots=True)
class RedundantTypecastRule:
    id = "redundant-typecast"
    description = (
        "Static type cast converts a value into the very same type. Remove the cast."
    )
    level = LintLevel.WARN

    def check(self, module: Module, context: LintContext) -> Iterable[LintDiagnostic]:  # noqa: ARG002
        for function in module.executable_functions:
            yield from self._check_function(function)

    def _check_function(self, function: Function) -> Iterable[LintDiagnostic]:
        for operator in function.operators:
            if operator.type != OperatorType.STATIC_TYPE_CAST:
                continue

            # Source type of a cast is known only to the typechecker (it emulates the
            # operand stack), so it is taken from the analysis metadata it left behind.
            # Operators that typechecker never reached (e.g code after early return)
            # carry no metadata and are skipped.
            meta = operator.tc_meta
            if not isinstance(meta, TypecastMeta):
                continue

            if not is_types_same(meta.a, meta.b, strategy="strict-same-type"):
                continue

            yield LintDiagnostic(
                rule_id=self.id,
                level=self.level,
                message=(
                    f"Redundant static type cast from `{meta.a}` to `{meta.b}` "
                    f"at {operator.token.location} "
                    f"(e.g type is strictly same so it is considered as redundant)"
                ),
                at=operator.token.location,
            )
