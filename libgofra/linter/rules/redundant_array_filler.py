from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from libgofra.hir.literals import ArrayLiteral
from libgofra.linter.diagnostics import LintDiagnostic, LintLevel
from libgofra.types.composite.array import ArrayType

if TYPE_CHECKING:
    from collections.abc import Iterable

    from libgofra.hir.module import Module
    from libgofra.hir.variable import Variable
    from libgofra.linter.context import LintContext


@dataclass(frozen=True, slots=True)
class RedundantArrayFillerRule:
    id = "redundant-array-filler"
    description = (
        "Array initializer has a filler value, but the array is already fully "
        "populated with explicit elements. The filler is never used."
    )
    level = LintLevel.WARN

    def check(self, module: Module, context: LintContext) -> Iterable[LintDiagnostic]:  # noqa: ARG002
        for variable in self._iter_candidate_variables(module):
            diag = self._check_variable(variable)
            if diag is not None:
                yield diag

    def _check_variable(self, variable: Variable) -> LintDiagnostic | None:
        if not isinstance(variable.initial_value, ArrayLiteral):
            return None
        if not isinstance(variable.type, ArrayType):
            return None
        filler = variable.initial_value.default
        if filler is None:
            return None

        explicit_count = len(variable.initial_value.elements)
        total_count = variable.type.elements_count

        # Compare only the *outer* dimension: nested arrays have nested literals,
        # which are not counted here (each nested element is one entry at this level).
        if explicit_count != total_count:
            return None

        return LintDiagnostic(
            rule_id=self.id,
            level=self.level,
            message=(
                f"Redundant array initializer filler for `{variable.name}` "
                f"at {variable.defined_at}: array is already fully populated "
                f"({explicit_count}/{total_count} elements). "
                f"Either remove the filler or expand the array size."
            ),
            at=variable.defined_at,
        )

    def _iter_candidate_variables(self, module: Module) -> Iterable[Variable]:
        yield from module.variables.values()
        for function in module.functions.values():
            if function.attrs.external:
                continue
            yield from function.variables.values()
