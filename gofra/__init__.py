"""Gofra programming language.

Provides toolchain including CLI, compiler etc.
"""

from .assembler import assemble_program
from .gofra import process_input_file

__all__ = [
    "assemble_program",
    "process_input_file",
]
