from gofra.targets import TargetArchitecture, TargetOperatingSystem

from .backends import CodeGeneratorBackend, generate_ARM64_MacOS_backend, generate_X86_Linux_backend
from .exceptions import CodegenUnsupportedBackendTargetPairError


def get_backend_for_target_pair(
    architecture: TargetArchitecture,
    operating_system: TargetOperatingSystem,
) -> CodeGeneratorBackend:
    match (architecture, operating_system):
        case (TargetArchitecture.ARM, TargetOperatingSystem.MACOS):
            return generate_ARM64_MacOS_backend
        case (TargetArchitecture.X86, TargetOperatingSystem.LINUX):
            return generate_X86_Linux_backend
        case _:
            raise CodegenUnsupportedBackendTargetPairError
