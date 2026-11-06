from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class COFFSection:
    """Specification for COFF/PE assembler section directives."""

    name: str
    flags: Sequence[str]

    def __str__(self) -> str:
        """Get COFF section directive for assembler."""
        return f'{self.name}, "{"".join(self.flags)}"'


COFF_SECTION_BSS = COFFSection(
    name=".bss",
    flags=("b", "w"),
)  # Uninitialized data

COFF_SECTION_DATA = COFFSection(
    name=".data",
    flags=("d", "w"),
)  # Initialized read-write data

COFF_SECTION_STRINGS = COFFSection(
    name=".rdata",
    flags=("r",),
)  # Read-only data (strings, constants)

COFF_SECTION_INSTRUCTIONS = COFFSection(
    name=".text",
    flags=("x", "r"),
)  # Executable code
