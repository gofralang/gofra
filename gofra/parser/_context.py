from __future__ import annotations

from collections import deque
from collections.abc import Iterable, MutableMapping, MutableSequence, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from gofra.lexer import Token
from gofra.parser.functions import Function
from gofra.typecheck.types import GofraType

from .exceptions import ParserEmptyInputTokensError
from .macros import Macro
from .operators import Operator, OperatorOperand, OperatorType


@dataclass(frozen=False)
class ParserContext:
    """Context for parsing which only required from internal usages."""

    parsing_from_path: Path
    include_search_directories: Iterable[Path]

    # Mostly immutable input source tokens
    tokens: deque[Token]

    # Resulting operators from parsing
    operators: MutableSequence[Operator] = field(default_factory=lambda: list())  # noqa: C408

    # Contextual data
    macros: MutableMapping[str, Macro] = field(default_factory=lambda: dict())  # noqa: C408
    functions: MutableMapping[str, Function] = field(default_factory=lambda: dict())  # noqa: C408
    context_stack: deque[tuple[int, Operator]] = field(default_factory=deque)
    included_source_paths: set[Path] = field(default_factory=set)

    current_operator: int = field(default=0)

    def __post_init__(self) -> None:
        if not self.tokens:
            raise ParserEmptyInputTokensError

        self.included_source_paths.add(self.parsing_from_path)

    def tokens_exhausted(self) -> bool:
        return len(self.tokens) == 0

    def has_context_stack(self) -> bool:
        return len(self.context_stack) > 0

    def new_macro(self, from_token: Token, name: str) -> Macro:
        macro = Macro(location=from_token.location, inner_tokens=[], name=name)
        self.macros[name] = macro
        return macro

    def new_function(
        self,
        from_token: Token,
        name: str,
        *,
        call_signature: Sequence[GofraType],
        return_type: GofraType | None,
        is_inline: bool,
        is_extern: bool,
    ) -> Function:
        function = Function(
            location=from_token.location,
            inner_tokens=[],
            inner_body=[],
            name=name,
            call_signature=call_signature,
            return_type=return_type,
            is_inline=is_inline,
            is_extern=is_extern,
        )
        self.functions[name] = function
        return function

    def expand_from_inline_block(self, inline_block: Macro | Function) -> None:
        if isinstance(inline_block, Function) and inline_block.is_extern:
            msg = "Cannot expand extern function."
            raise ValueError(msg)
        self.tokens.extend(deque(reversed(inline_block.inner_tokens)))

    def pop_context_stack(self) -> tuple[int, Operator]:
        return self.context_stack.pop()

    def push_new_operator(
        self,
        type: OperatorType,  # noqa: A002
        token: Token,
        operand: OperatorOperand,
        *,
        is_contextual: bool,
    ) -> None:
        operator = Operator(
            type=type,
            token=token,
            operand=operand,
            has_optimizations=False,
        )
        self.operators.append(operator)
        if is_contextual:
            self.context_stack.append((self.current_operator, operator))
        self.current_operator += 1
