from dataclasses import dataclass, field

from libgofra.linter.diagnostics import LintLevel
from libgofra.linter.rule import LintRule


@dataclass
class LintConfig:
    overrides: dict[str, LintLevel] = field(default_factory=dict)

    def level_for(self, rule: LintRule) -> LintLevel:
        return self.overrides.get(rule.id, rule.level)

    def is_enabled(self, rule: LintRule) -> bool:
        return self.level_for(rule) != LintLevel.ALLOW
