from gofra.codegen.targets import TARGET_T

from .backends import (
    CodeGeneratorBackend,
    generate_aarch64_macos_backend,
    generate_amd64_linux_backend,
)
from .exceptions import CodegenUnsupportedBackendTargetPairError


def get_backend_for_target(
    target: TARGET_T,
) -> CodeGeneratorBackend:
    """Get code generator backend for specified ARCHxOS pair."""
    match target:
        case "aarch64-darwin":
            return generate_aarch64_macos_backend
        case "x86_64-linux":
            return generate_amd64_linux_backend
        case _:
            raise CodegenUnsupportedBackendTargetPairError(target=target)
