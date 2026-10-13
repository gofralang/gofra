from typing import TYPE_CHECKING

from libgofra.assembler.assembler import assemble_object_files
from libgofra.driver.artifact import AssemblyArtifact, ObjectArtifact
from libgofra.driver.diagnostics import DiagnosticConsumer
from libgofra.driver.layout import BuildLayout
from libgofra.driver.request import CompilationRequest

if TYPE_CHECKING:
    from pathlib import Path


def driver_run_assembler_stage(
    request: CompilationRequest,
    layout: BuildLayout,
    assembly: AssemblyArtifact,
    diag: DiagnosticConsumer,
) -> ObjectArtifact:
    if not request.output_format.needs_assembler:
        return ObjectArtifact(
            assembly=assembly,
            modules_objects={},
        )

    modules_objects: dict[Path, Path] = {}
    root_module = assembly.frontend.root
    with diag.timer("Assembler"):
        modules_objects[root_module.path] = layout.root_object

        for mod in root_module.visit_dependencies(include_self=False):
            modules_objects[mod.path] = layout.module_object(mod)

        diag.info(f"Calling assembler for batch of {len(modules_objects)} artifacts...")

        assembly_targets = [
            (assembly.modules_assembly[mod_path], mod_object_path)
            for mod_path, mod_object_path in modules_objects.items()
        ]
        assembler_processes = assemble_object_files(
            file_pairs=assembly_targets,
            target=request.target,
            extra_flags=request.assembler_flags,
            debug_information=request.debug_symbols,
        )
        for process in assembler_processes:
            process.check_returncode()
            diag.command(process.args)

    return ObjectArtifact(
        assembly=assembly,
        modules_objects=modules_objects,
    )
