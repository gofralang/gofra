"""Gofra programming language.

Provides toolchain including CLI, compiler etc.
"""

from .assembler import assemble_executable
from .codegen.targets import TargetArchitecture, TargetOperatingSystem
from .gofra import process_input_file

__all__ = [
    "TargetArchitecture",
    "TargetOperatingSystem",
    "assemble_executable",
    "process_input_file",
]
