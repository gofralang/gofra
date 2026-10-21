from libgofra.exceptions import GofraError
from libgofra.linter.diagnostics import LintDiagnostic


class LinterRuleDeniedError(GofraError):
    def __init__(self, diagnostic: LintDiagnostic) -> None:
        self.diagnostic = diagnostic

    def __repr__(self) -> str:
        return (
            f"Lint rule `{self.diagnostic.rule_id}` denied:\n\n"
            f"{self.diagnostic.message}\n\n[{self.diagnostic.rule_id}]\n{self.generic_error_name}"
        )
