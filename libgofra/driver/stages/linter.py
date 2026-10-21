from libgofra.driver.artifact import FrontendArtifact
from libgofra.driver.diagnostics import DiagnosticConsumer
from libgofra.driver.request import CompilationRequest
from libgofra.linter.diagnostics import LintLevel
from libgofra.linter.error import LinterRuleDeniedError
from libgofra.linter.registry import get_default_registry
from libgofra.linter.runner import LintRunner


def driver_run_linter_stage(
    request: CompilationRequest,
    frontend: FrontendArtifact,
    diag: DiagnosticConsumer,
) -> FrontendArtifact:

    with diag.timer("Linter"):
        runner = LintRunner(
            registry=get_default_registry(),
            config=request.lint_config,
        )
        for mod in frontend.root.visit_dependencies(include_self=True):
            for linter_diag in runner.check(mod):
                if linter_diag.level == LintLevel.DENY:
                    raise LinterRuleDeniedError(linter_diag)
                if not request.display_lint_warnings:
                    continue
                diag.warning(linter_diag.message)

    return frontend
