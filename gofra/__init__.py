"""Gofra programming language.

Provides toolchain including CLI, compiler etc.
"""

from .assembler import assemble_executable
from .gofra import process_input_file

__all__ = [
    "assemble_executable",
    "process_input_file",
]
