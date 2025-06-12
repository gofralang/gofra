"""Code generation backend module.

Provides code generation backends (codegens) for emitting assembly from IR.
"""

from .aarch64_macos import generate_aarch64_macos_backend
from .amd64_linux import generate_amd64_linux_backend
from .base import CodeGeneratorBackend

__all__ = [
    "CodeGeneratorBackend",
    "generate_aarch64_macos_backend",
    "generate_amd64_linux_backend",
]
