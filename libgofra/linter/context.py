from dataclasses import dataclass, field

from libgofra.hir.module import Module
from libgofra.linter.references import References
from libgofra.optimizer.helpers.call_graph import CallGraph


@dataclass
class LintContext:
    module: Module
    call_graph: CallGraph | None = None
    references: References = field(default_factory=References)
