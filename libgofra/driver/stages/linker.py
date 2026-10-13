from libgofra.driver.artifact import ExecutableArtifact, LibraryArtifact, ObjectArtifact
from libgofra.driver.diagnostics import DiagnosticConsumer
from libgofra.driver.request import CompilationRequest, DriverOutputFormat
from libgofra.linker.command_composer import resolve_linker_command_composer
from libgofra.linker.entry_point import LINKER_EXPECTED_ENTRY_POINT
from libgofra.linker.linker import link_object_files
from libgofra.linker.pkgconfig.pkgconfig import resolve_library_search_paths


def driver_run_linker_stage(
    request: CompilationRequest,
    artifact: ObjectArtifact,
    diag: DiagnosticConsumer,
) -> ExecutableArtifact | LibraryArtifact | None:
    if not request.output_format.needs_linkage:
        return None

    with diag.timer("Linker"):
        linker_backend = resolve_linker_command_composer(
            backend=request.linker_backend,
            target=request.target,
        )
        libraries_search_paths = resolve_library_search_paths(
            request.linker_libraries_search_paths,
            request.linker_libraries,
            resolve_with_pkgconfig=request.linker_resolve_libraries_with_pkgconfig,
        )

        linker_process = link_object_files(
            objects=artifact.modules_objects.values(),
            target=request.target,
            output=request.output_filepath,
            libraries=request.linker_libraries,
            output_format=request.output_format.to_linker_output_format(),
            additional_flags=request.linker_additional_flags,
            libraries_search_paths=libraries_search_paths,
            profile=request.linker_profile,
            linker_backend=linker_backend,
            linker_executable=request.linker_executable,
            cache_directory=request.build_cache_dir,
            executable_entry_point_symbol=LINKER_EXPECTED_ENTRY_POINT,
        )
        diag.command(linker_process.args)
        linker_process.check_returncode()

    if request.output_format == DriverOutputFormat.EXECUTABLE:
        return ExecutableArtifact(
            executable_path=request.output_filepath,
            objects=artifact,
        )

    return LibraryArtifact(
        library_path=request.output_filepath,
        objects=artifact,
    )
