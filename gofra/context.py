from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from gofra.parser.functions import Function


@dataclass(frozen=False)
class ProgramContext:
    """Context for program which only required for internal usages.

    Acquired from parser context and mutable within next stages.
    """

    functions: MutableMapping[str, Function]
    memories: MutableMapping[str, int]
    entry_point: Function
