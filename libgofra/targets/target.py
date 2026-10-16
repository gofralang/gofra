from dataclasses import dataclass
from typing import Literal

type Triplet = Literal[
    "amd64-unknown-linux",
    "amd64-unknown-windows",
    "amd64-apple-darwin",
    "arm64-apple-darwin",
    "wasm32-unknown-none",
]


@dataclass(eq=True)
class Target:
    """Specifications for target build host."""

    status: Literal["stable", "experimental"]

    # Conventional triplet for that target for comparisons
    triplet: Triplet

    # Based on triplet
    architecture: Literal["AMD64", "ARM64", "WASM32"]
    vendor: Literal["unknown", "apple"]
    operating_system: Literal["Darwin", "Linux", "Windows", "None"]

    cpu_pointer_width: Literal[8]

    endianness: Literal["little", "big"]

    file_executable_suffix: Literal["", ".exe", ".wasm"]
    file_library_static_suffix: Literal[".a", ".lib", ".wasm"]
    file_library_dynamic_suffix: Literal[".dylib", ".so", ".dll", ".wasm"]
    file_assembly_suffix: Literal[".s", ".asm", ".wat"]
    file_object_suffix: Literal[".o", ".obj", ".wasm"]

    @property
    def simple_name(self) -> str:
        return f"{self.operating_system.lower()}/{self.architecture.lower()}"

    @staticmethod
    def from_triplet(triplet: Triplet) -> "Target":
        match triplet:
            case "amd64-apple-darwin":
                return Target(
                    status="experimental",
                    triplet=triplet,
                    architecture="AMD64",
                    vendor="apple",
                    operating_system="Darwin",
                    cpu_pointer_width=8,
                    file_executable_suffix="",
                    file_library_static_suffix=".a",
                    file_library_dynamic_suffix=".dylib",
                    file_object_suffix=".o",
                    file_assembly_suffix=".s",
                    endianness="little",
                )
            case "arm64-apple-darwin":
                return Target(
                    status="stable",
                    triplet=triplet,
                    vendor="apple",
                    architecture="ARM64",
                    operating_system="Darwin",
                    cpu_pointer_width=8,
                    file_executable_suffix="",
                    file_library_static_suffix=".a",
                    file_library_dynamic_suffix=".dylib",
                    file_object_suffix=".o",
                    file_assembly_suffix=".s",
                    endianness="little",
                )
            case "amd64-unknown-windows":
                return Target(
                    status="experimental",
                    triplet=triplet,
                    vendor="unknown",
                    architecture="AMD64",
                    operating_system="Windows",
                    cpu_pointer_width=8,
                    file_executable_suffix=".exe",
                    file_library_static_suffix=".lib",
                    file_library_dynamic_suffix=".dll",
                    file_object_suffix=".obj",
                    file_assembly_suffix=".asm",
                    endianness="little",
                )
            case "amd64-unknown-linux":
                return Target(
                    status="experimental",
                    triplet=triplet,
                    vendor="unknown",
                    architecture="AMD64",
                    operating_system="Linux",
                    cpu_pointer_width=8,
                    file_executable_suffix="",
                    file_library_static_suffix=".a",
                    file_library_dynamic_suffix=".so",
                    file_object_suffix=".o",
                    endianness="little",
                    file_assembly_suffix=".s",
                )
            case "wasm32-unknown-none":
                return Target(
                    status="experimental",
                    triplet=triplet,
                    vendor="unknown",
                    architecture="WASM32",
                    operating_system="None",
                    cpu_pointer_width=8,
                    file_executable_suffix=".wasm",
                    file_library_static_suffix=".wasm",
                    file_library_dynamic_suffix=".wasm",
                    file_object_suffix=".wasm",
                    endianness="little",
                    file_assembly_suffix=".wat",
                )
