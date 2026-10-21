# libgofra/linter/tests/test_config.py

from __future__ import annotations

from typing import TYPE_CHECKING

from libgofra.linter.config import LintConfig
from libgofra.linter.diagnostics import LintLevel

if TYPE_CHECKING:
    from libgofra.linter.rule import LintRule


class _FakeRule:
    def __init__(self, rule_id: str, level: LintLevel) -> None:
        self.id = rule_id
        self.level = level


def test_default_config_keeps_rule_level() -> None:
    config = LintConfig()
    rule = _FakeRule("some-rule", LintLevel.WARN)  # type: ignore[arg-type]

    assert config.level_for(rule) == LintLevel.WARN
    assert config.is_enabled(rule)


def test_override_replaces_rule_level() -> None:
    config = LintConfig(overrides={"some-rule": LintLevel.DENY})
    rule = _FakeRule("some-rule", LintLevel.WARN)  # type: ignore[arg-type]

    assert config.level_for(rule) == LintLevel.DENY
    assert config.is_enabled(rule)


def test_allow_override_disables_rule() -> None:
    config = LintConfig(overrides={"some-rule": LintLevel.ALLOW})
    rule = _FakeRule("some-rule", LintLevel.WARN)  # type: ignore[arg-type]

    assert config.level_for(rule) == LintLevel.ALLOW
    assert not config.is_enabled(rule)


def test_override_does_not_affect_other_rules() -> None:
    config = LintConfig(overrides={"some-rule": LintLevel.DENY})
    other = _FakeRule("other-rule", LintLevel.WARN)  # type: ignore[arg-type]

    assert config.level_for(other) == LintLevel.WARN


def test_config_is_protocol_compatible_with_lint_rule() -> None:
    # LintConfig is typed against the LintRule protocol, not a concrete class
    config = LintConfig(overrides={"some-rule": LintLevel.DENY})
    rule: LintRule = _FakeRule("some-rule", LintLevel.WARN)  # type: ignore[assignment]

    assert config.level_for(rule) == LintLevel.DENY
