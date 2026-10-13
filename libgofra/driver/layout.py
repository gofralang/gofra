from dataclasses import dataclass
from pathlib import Path

from libgofra.driver.cache.directory import prepare_build_cache_directory
from libgofra.driver.incremental import get_module_hash
from libgofra.hir.module import Module
from libgofra.targets import Target


@dataclass
class BuildLayout:
    cache_dir: Path
    output: Path
    target: Target

    def prepare(self) -> None:
        prepare_build_cache_directory(self.cache_dir)

    @property
    def base(self) -> Path:
        return self.cache_dir / self.target.triplet

    @property
    def deps(self) -> Path:
        return self.base / f"{self.output.stem}$deps"

    @property
    def root_assembly(self) -> Path:
        return (self.base / self.output.name).with_suffix(
            self.target.file_assembly_suffix,
        )

    @property
    def root_object(self) -> Path:
        return (self.base / self.output.name).with_suffix(
            self.target.file_object_suffix,
        )

    def module_assembly(self, mod: Module) -> Path:
        return (self.deps / get_module_hash(mod)).with_suffix(
            self.target.file_assembly_suffix,
        )

    def module_object(self, mod: Module) -> Path:
        return (self.deps / get_module_hash(mod)).with_suffix(
            self.target.file_object_suffix,
        )
