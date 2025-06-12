from gofra.codegen.targets import TARGET_T
from gofra.exceptions import GofraError


class CodegenUnsupportedBackendTargetPairError(GofraError):
    def __init__(
        self,
        *args: object,
        target: TARGET_T,
    ) -> None:
        super().__init__(*args)
        self.target = target

    def __repr__(self) -> str:
        return f"""Code generation failed

Unsupported target '{self.target}'!
Please read documentation to find available target pairs!
"""
