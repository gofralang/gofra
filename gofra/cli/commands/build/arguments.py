from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal, assert_never

from libgofra.codegen.config import CodegenConfig
from libgofra.driver.request import CompilationRequest, DriverOutputFormat
from libgofra.exceptions import GofraError
from libgofra.linker.output_format import LinkerOutputFormat
from libgofra.linker.profile import LinkerProfile
from libgofra.linter.config import LintConfig
from libgofra.optimizer.config import OptimizerConfig
from libgofra.targets.target import Target


class BuildOutputFormat(StrEnum):
    ASSEMBLY = "assembly"
    OBJECT = "object"
    LIBRARY = "library"
    EXECUTABLE = "executable"

    @property
    def needs_assembler(self) -> bool:
        return self != BuildOutputFormat.ASSEMBLY

    @property
    def needs_linkage(self) -> bool:
        return self not in (BuildOutputFormat.ASSEMBLY, BuildOutputFormat.OBJECT)

    def to_linker_output_format(self) -> LinkerOutputFormat:
        match self:
            case BuildOutputFormat.EXECUTABLE:
                return LinkerOutputFormat.EXECUTABLE
            case BuildOutputFormat.LIBRARY:
                return LinkerOutputFormat.LIBRARY
            case BuildOutputFormat.OBJECT:
                return LinkerOutputFormat.OBJECT
            case BuildOutputFormat.ASSEMBLY:
                msg = "cannot output assembly from linker!"
                raise GofraError(msg)
            case _:
                assert_never(self)


@dataclass(slots=True, frozen=True)
class BuildArguments:
    """Arguments from argument parser provided for build command."""

    source_filepath: Path
    output_filepath: Path
    output_format: BuildOutputFormat
    output_file_is_specified: bool  # Internal flag

    include_paths: list[Path]
    definitions: dict[str, str]

    hir: bool
    preprocess_only: bool
    call_graph_only: bool

    verbose: bool
    show_commands: bool

    target: Target

    display_lint_warnings: bool
    lint_config: LintConfig

    build_cache_dir: Path
    delete_build_cache: bool

    executable_entry_point: str

    cli_debug_user_friendly_errors: bool

    runtime_array_oob_checks: bool

    linker_profile: LinkerProfile
    linker_additional_flags: list[str]
    linker_libraries: list[str]
    linker_libraries_search_paths: list[Path]
    linker_backend: Literal["gnu-ld", "apple-ld"] | None
    linker_resolve_libraries_with_pkgconfig: bool
    linker_executable: Path | None

    debug_symbols: bool
    incremental_compilation: bool
    optimizer: OptimizerConfig

    assembler_flags: list[str]

    codegen_config: CodegenConfig

    def to_compilation_request(self) -> CompilationRequest:
        return CompilationRequest(
            source_filepath=self.source_filepath,
            include_paths=self.include_paths,
            definitions=dict(self.definitions),
            target=self.target,
            output_filepath=self.output_filepath,
            output_format=DriverOutputFormat(self.output_format),
            executable_entry_point=self.executable_entry_point,
            runtime_array_oob_checks=self.runtime_array_oob_checks,
            display_lint_warnings=self.display_lint_warnings,
            lint_config=self.lint_config,
            optimizer=self.optimizer,
            codegen_config=self.codegen_config,
            debug_symbols=self.debug_symbols,
            assembler_flags=self.assembler_flags,
            linker_profile=self.linker_profile,
            linker_additional_flags=self.linker_additional_flags,
            linker_libraries=self.linker_libraries,
            linker_libraries_search_paths=self.linker_libraries_search_paths,
            linker_backend=self.linker_backend,
            linker_resolve_libraries_with_pkgconfig=self.linker_resolve_libraries_with_pkgconfig,
            linker_executable=self.linker_executable,
            build_cache_dir=self.build_cache_dir,
            delete_build_cache=self.delete_build_cache,
            incremental_compilation=self.incremental_compilation,
        )
