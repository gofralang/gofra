from libgofra.driver.artifact import FrontendArtifact
from libgofra.driver.diagnostics import DiagnosticConsumer
from libgofra.driver.request import CompilationRequest
from libgofra.optimizer.pipeline import create_optimizer_pipeline


def driver_run_optimize_stage(
    request: CompilationRequest,
    frontend: FrontendArtifact,
    diag: DiagnosticConsumer,
) -> FrontendArtifact:
    with diag.timer("Frontend (optimizer)"):
        diag.info(
            f"Applying optimizer pipeline (From base optimizer level: {request.optimizer.level})...",
        )

        pipeline = create_optimizer_pipeline(request.optimizer)

        for dependant_module in frontend.root.visit_dependencies(include_self=False):
            for optimizer_pass, _ in pipeline:
                optimizer_pass(dependant_module)

        # Perform root optimizations last - high level optimizations after dependencies
        for optimizer_pass, _ in pipeline:
            optimizer_pass(frontend.root)

    return frontend
