"""Assembler package that links and assembles generated code into final executable.

Tools used for assembly is different for specified target
"""

from .assembler import assemble_executable

__all__ = ["assemble_executable"]
