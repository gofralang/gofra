from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING

from libgofra.linter.diagnostics import LintDiagnostic, LintLevel
from libgofra.types.composite.structure import StructureType
from libgofra.types.reordering import reorder_type_fields

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from libgofra.hir.module import Module
    from libgofra.linter.context import LintContext


@dataclass(frozen=True, slots=True)
class StructReorderHintRule:
    id = "struct-reorder-hint"
    description = (
        "Structure fields can be reordered to reduce padding. "
        "Consider adding `reorder` attribute."
    )
    level = LintLevel.WARN

    def check(self, module: Module, context: LintContext) -> Iterable[LintDiagnostic]:  # noqa: ARG002
        for struct in self._iter_candidate_structures(module):
            new_order, has_possible_reorder = reorder_type_fields(
                unordered=struct.natural_order,
                fields=struct.natural_fields,
            )
            if not has_possible_reorder:
                continue

            reordered_size = self._size_with_order(struct, new_order)
            diff = struct.size_in_bytes - reordered_size
            if diff <= 0:
                continue

            yield LintDiagnostic(
                rule_id=self.id,
                level=self.level,
                message=(
                    f"Struct `{struct.name}` has possible field reordering! "
                    f"Current order wastes {diff} bytes of padding "
                    f"({struct.size_in_bytes}b unordered, {reordered_size}b reordered). "
                    f"Add `reorder` attribute to the struct definition."
                ),
            )

    def _iter_candidate_structures(
        self,
        module: Module,
    ) -> Iterable[StructureType]:
        for t in module.types.values():
            if not isinstance(t, StructureType):
                continue
            if t.is_reordering_allowed or t.is_packed:
                continue
            yield t

    def _size_with_order(
        self,
        struct: StructureType,
        order: Sequence[str],
    ) -> int:
        """Compute struct size if fields were laid out in `order`."""
        copy = deepcopy(struct)
        copy.backpatch(fields=struct.natural_fields, order=order)
        return copy.size_in_bytes
