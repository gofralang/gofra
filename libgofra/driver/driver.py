from __future__ import annotations

from typing import TYPE_CHECKING

from libgofra.driver.layout import BuildLayout
from libgofra.driver.stages.assembler import driver_run_assembler_stage
from libgofra.driver.stages.codegen import driver_run_codegen_stage
from libgofra.driver.stages.frontend import driver_run_frontend_stage
from libgofra.driver.stages.linker import driver_run_linker_stage
from libgofra.driver.stages.linter import driver_run_linter_stage
from libgofra.driver.stages.optimize import driver_run_optimize_stage
from libgofra.driver.stages.typecheck import driver_run_typecheck_stage

if TYPE_CHECKING:
    from libgofra.driver.artifact import Artifact
    from libgofra.driver.diagnostics import DiagnosticConsumer
    from libgofra.driver.request import CompilationRequest


class Driver:
    def __init__(self, request: CompilationRequest, diag: DiagnosticConsumer) -> None:
        self._request = request
        self._diag = diag
        self._layout = BuildLayout(
            cache_dir=request.build_cache_dir,
            output=request.output_filepath,
            target=request.target,
        )

    def run(self) -> Artifact:
        request = self._request
        diag = self._diag
        layout = self._layout

        layout.prepare()

        frontend = driver_run_frontend_stage(request, diag)
        frontend = driver_run_typecheck_stage(request, frontend, diag)
        frontend = driver_run_linter_stage(request, frontend, diag)
        frontend = driver_run_optimize_stage(request, frontend, diag)
        assembly = driver_run_codegen_stage(request, layout, frontend, diag)
        objects = driver_run_assembler_stage(request, layout, assembly, diag)
        linked = driver_run_linker_stage(request, objects, diag)

        return linked or objects

    @property
    def layout(self) -> BuildLayout:
        return self._layout
