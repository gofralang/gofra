from pathlib import Path

from libgofra.codegen import generate_code_for_assembler
from libgofra.driver.artifact import AssemblyArtifact, FrontendArtifact
from libgofra.driver.diagnostics import DiagnosticConsumer
from libgofra.driver.layout import BuildLayout
from libgofra.driver.request import CompilationRequest
from libgofra.hir.module import Module


def driver_run_codegen_stage(
    request: CompilationRequest,
    layout: BuildLayout,
    frontend: FrontendArtifact,
    diag: DiagnosticConsumer,
) -> AssemblyArtifact:

    modules_assembly = {}
    with diag.timer("Codegen"):
        _emit_module_assembly(request, diag, frontend.root, layout.root_assembly)
        modules_assembly[frontend.root.path] = layout.root_assembly

        for module in frontend.root.visit_dependencies(include_self=False):
            module_assembly_path = layout.module_assembly(module)

            _emit_module_assembly(request, diag, module, module_assembly_path)
            modules_assembly[module.path] = module_assembly_path

    modules_count = len(modules_assembly)
    diag.info(f"Generated {modules_count} assembly files for {modules_count} modules")

    return AssemblyArtifact(
        frontend=frontend,
        modules_assembly=modules_assembly,
    )


def _emit_module_assembly(
    request: CompilationRequest,
    diag: DiagnosticConsumer,
    module: Module,
    output: Path,
) -> None:
    generate_code_for_assembler(
        output,
        module,
        request.target,
        config=request.codegen_config,
        on_warning=diag.warning,
    )
