from dataclasses import dataclass
from pathlib import Path

from libgofra.hir.module import Module


@dataclass(frozen=True)
class Artifact: ...


@dataclass(frozen=True)
class FrontendArtifact(Artifact):
    root: Module


@dataclass(frozen=True)
class AssemblyArtifact(Artifact):
    frontend: FrontendArtifact
    modules_assembly: dict[Path, Path]


@dataclass(frozen=True)
class ObjectArtifact(Artifact):
    assembly: AssemblyArtifact
    modules_objects: dict[Path, Path]


@dataclass(frozen=True)
class ExecutableArtifact(Artifact):
    executable_path: Path
    objects: ObjectArtifact


@dataclass(frozen=True)
class LibraryArtifact(Artifact):
    library_path: Path
    objects: ObjectArtifact
