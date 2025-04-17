from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import MutableMapping, MutableSequence

    from gofra.parser.functions import Function
    from gofra.parser.operators import Operator


@dataclass(frozen=False)
class ProgramContext:
    """Context for program which only required for internal usages.

    Acquired from parser context and mutable within next stages.
    """

    # Resulting operators from parsing
    operators: MutableSequence[Operator] = field(default_factory=lambda: list())  # noqa: C408
    functions: MutableMapping[str, Function] = field(default_factory=lambda: dict())  # noqa: C408
