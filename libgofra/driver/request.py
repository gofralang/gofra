from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Literal, assert_never

from libgofra.codegen.config import CodegenConfig
from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation
from libgofra.linker.output_format import LinkerOutputFormat
from libgofra.linker.profile import LinkerProfile
from libgofra.linter.config import LintConfig
from libgofra.optimizer.config import OptimizerConfig
from libgofra.targets.target import Target


class DriverOutputFormat(StrEnum):
    ASSEMBLY = "assembly"
    OBJECT = "object"
    LIBRARY = "library"
    EXECUTABLE = "executable"

    @property
    def needs_assembler(self) -> bool:
        return self != DriverOutputFormat.ASSEMBLY

    @property
    def needs_linkage(self) -> bool:
        return self not in (DriverOutputFormat.ASSEMBLY, DriverOutputFormat.OBJECT)

    def to_linker_output_format(self) -> LinkerOutputFormat:
        match self:
            case DriverOutputFormat.EXECUTABLE:
                return LinkerOutputFormat.EXECUTABLE
            case DriverOutputFormat.LIBRARY:
                return LinkerOutputFormat.LIBRARY
            case DriverOutputFormat.OBJECT:
                return LinkerOutputFormat.OBJECT
            case DriverOutputFormat.ASSEMBLY:
                msg = "cannot output assembly from linker!"
                raise GofraError(msg)
            case _:
                assert_never(self)


@dataclass(slots=True, frozen=True)
class CompilationRequest:
    source_filepath: Path
    include_paths: list[Path]
    definitions: dict[str, str]

    target: Target
    output_filepath: Path
    output_format: DriverOutputFormat

    executable_entry_point: str
    runtime_array_oob_checks: bool

    display_lint_warnings: bool

    optimizer: OptimizerConfig

    codegen_config: CodegenConfig
    debug_symbols: bool

    assembler_flags: list[str]

    linker_profile: LinkerProfile
    linker_additional_flags: list[str]
    linker_libraries: list[str]
    linker_libraries_search_paths: list[Path]
    linker_backend: Literal["gnu-ld", "apple-ld"] | None
    linker_resolve_libraries_with_pkgconfig: bool
    linker_executable: Path | None

    build_cache_dir: Path
    delete_build_cache: bool
    incremental_compilation: bool
    definitions_location: TokenLocation = field(default_factory=TokenLocation.cli)

    lint_config: LintConfig = field(default_factory=LintConfig)

    def deps_dir(self, root_artifact_path: Path) -> Path:
        return root_artifact_path.parent / f"{self.source_filepath.stem}$deps"
