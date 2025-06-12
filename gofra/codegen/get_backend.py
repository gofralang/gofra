from gofra.codegen.targets import TargetArchitecture, TargetOperatingSystem

from .backends import (
    CodeGeneratorBackend,
    generate_aarch64_macos_backend,
    generate_amd64_linux_backend,
)
from .exceptions import CodegenUnsupportedBackendTargetPairError


def get_backend_for_target_pair(
    architecture: TargetArchitecture,
    operating_system: TargetOperatingSystem,
) -> CodeGeneratorBackend:
    """Get code generator backend for specified ARCHxOS pair."""
    match (architecture, operating_system):
        case (TargetArchitecture.ARM, TargetOperatingSystem.MACOS):
            return generate_aarch64_macos_backend
        case (TargetArchitecture.AMD, TargetOperatingSystem.LINUX):
            return generate_amd64_linux_backend
        case _:
            raise CodegenUnsupportedBackendTargetPairError(
                architecture=architecture,
                operating_system=operating_system,
            )
