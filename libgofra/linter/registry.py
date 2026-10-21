# libgofra/linter/registry.py

from __future__ import annotations

from typing import TYPE_CHECKING

from libgofra.linter.rules.empty_function_body import EmptyFunctionBodyRule
from libgofra.linter.rules.redundant_array_filler import RedundantArrayFillerRule
from libgofra.linter.rules.redundant_typecast import RedundantTypecastRule
from libgofra.linter.rules.struct_reorder_hint import StructReorderHintRule
from libgofra.linter.rules.unused_global_variable import UnusedGlobalVariableRule
from libgofra.linter.rules.unused_local_variable import UnusedLocalVariableRule
from libgofra.linter.rules.unused_parameter import UnusedParameterRule
from libgofra.linter.rules.unused_private_function import UnusedPrivateFunctionRule

if TYPE_CHECKING:
    from collections.abc import Iterable

    from libgofra.linter.rule import LintRule


class LintRegistry:
    _rules: dict[str, LintRule]

    def __init__(self) -> None:
        self._rules = {}

    def register(self, rule: LintRule) -> None:
        if rule.id in self._rules:
            msg = f"Lint rule `{rule.id}` is already registered"
            raise ValueError(msg)
        self._rules[rule.id] = rule

    def get(self, rule_id: str) -> LintRule | None:
        return self._rules.get(rule_id)

    def all(self) -> Iterable[LintRule]:
        return self._rules.values()


def get_default_registry() -> LintRegistry:
    registry = LintRegistry()

    registry.register(RedundantArrayFillerRule())
    registry.register(RedundantTypecastRule())
    registry.register(StructReorderHintRule())
    registry.register(EmptyFunctionBodyRule())
    registry.register(UnusedGlobalVariableRule())
    registry.register(UnusedLocalVariableRule())
    registry.register(UnusedParameterRule())
    registry.register(UnusedPrivateFunctionRule())

    return registry
