from dataclasses import dataclass
from enum import Enum, auto

from libgofra.lexer.tokens import TokenLocation


class LintLevel(Enum):
    ALLOW = auto()  # Do nothing
    WARN = auto()  # warning, continue compilation
    DENY = auto()  # error, abort compilation


@dataclass(frozen=True, slots=True)
class LintDiagnostic:
    rule_id: str  # "unused-variable"

    level: LintLevel

    message: str
    at: TokenLocation | None = None
