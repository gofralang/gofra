from libgofra.driver.artifact import FrontendArtifact
from libgofra.driver.diagnostics import DiagnosticConsumer
from libgofra.driver.request import CompilationRequest, DriverOutputFormat
from libgofra.typecheck import validate_type_safety
from libgofra.typecheck.typechecker import on_lint_warning_suppressed


def driver_run_typecheck_stage(
    request: CompilationRequest,
    frontend: FrontendArtifact,
    diag: DiagnosticConsumer,
) -> FrontendArtifact:
    if request.skip_typecheck:
        return frontend

    on_lint_waring = (
        diag.warning if request.display_lint_warnings else on_lint_warning_suppressed
    )
    is_executable = request.output_format == DriverOutputFormat.EXECUTABLE
    with diag.timer("Frontend (typecheck + lint)"):
        for mod in frontend.root.visit_dependencies(include_self=True):
            is_root_mod = mod is frontend.root
            must_has_entry_point = (
                is_root_mod and is_executable
            )  # Main required for root module and only if executable
            validate_type_safety(
                mod,
                on_lint_warning=on_lint_waring,
                strict_expect_entry_point=must_has_entry_point,
                entry_point_name=request.executable_entry_point,
            )

    return frontend
