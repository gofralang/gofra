from gofra.exceptions import GofraError
from gofra.targets import TargetArchitecture, TargetOperatingSystem


class CodegenUnsupportedBackendTargetPairError(GofraError):
    def __init__(
        self,
        *args: object,
        architecture: TargetArchitecture,
        operating_system: TargetOperatingSystem,
    ) -> None:
        super().__init__(*args)
        self.architecture = architecture
        self.operating_system = operating_system

    def __repr__(self) -> str:
        return f"""Code generation failed

Unsupported backend target pair ({self.architecture.name} x {self.operating_system.name})!
Please read documentation to find available target pairs!
"""
