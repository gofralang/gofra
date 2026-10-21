from collections.abc import Iterable
from dataclasses import dataclass, replace

from libgofra.hir.module import Module
from libgofra.linter.config import LintConfig
from libgofra.linter.context import LintContext
from libgofra.linter.diagnostics import LintDiagnostic
from libgofra.linter.references import collect_references
from libgofra.linter.registry import LintRegistry
from libgofra.optimizer.helpers.call_graph import CallGraph


@dataclass
class LintRunner:
    registry: LintRegistry
    config: LintConfig

    def check(self, module: Module) -> Iterable[LintDiagnostic]:
        context = self._build_context(module)
        diagnostics: list[LintDiagnostic] = []
        for rule in self.registry.all():
            if not self.config.is_enabled(rule):
                continue
            level = self.config.level_for(rule)
            yield from [
                replace(diag, level=level) for diag in rule.check(module, context)
            ]

        return diagnostics

    def _build_context(self, module: Module) -> LintContext:
        call_graph = CallGraph(module)
        references = collect_references(module)
        return LintContext(module=module, call_graph=call_graph, references=references)
