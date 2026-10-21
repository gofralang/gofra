# gofra/cli/commands/build/tests/test_lint_config.py

from argparse import Namespace

import pytest

from gofra.cli.commands.build.parser import _process_lint_config
from libgofra.linter.diagnostics import LintLevel


def _args(
    *,
    allow: list[str] | None = None,
    deny: list[str] | None = None,
) -> Namespace:
    return Namespace(lint_allow=allow or [], lint_deny=deny or [])


def test_no_overrides_by_default() -> None:
    config = _process_lint_config(_args())

    assert config.overrides == {}


def test_allow_disables_rule() -> None:
    config = _process_lint_config(_args(allow=["unused-parameter"]))

    assert config.overrides == {"unused-parameter": LintLevel.ALLOW}


def test_deny_promotes_rule_to_error() -> None:
    config = _process_lint_config(_args(deny=["unused-parameter"]))

    assert config.overrides == {"unused-parameter": LintLevel.DENY}


def test_multiple_rules_are_supported() -> None:
    config = _process_lint_config(
        _args(allow=["unused-parameter"], deny=["redundant-typecast"]),
    )

    assert config.overrides == {
        "unused-parameter": LintLevel.ALLOW,
        "redundant-typecast": LintLevel.DENY,
    }


def test_deny_wins_over_allow_for_the_same_rule() -> None:
    config = _process_lint_config(
        _args(allow=["unused-parameter"], deny=["unused-parameter"]),
    )

    assert config.overrides == {"unused-parameter": LintLevel.DENY}


def test_unknown_rule_is_rejected() -> None:
    with pytest.raises(SystemExit):
        _process_lint_config(_args(deny=["unuse-parameter"]))


def test_unknown_rule_in_allow_is_rejected() -> None:
    with pytest.raises(SystemExit):
        _process_lint_config(_args(allow=["no-such-rule"]))
