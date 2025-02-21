from collections import deque
from collections.abc import MutableMapping, MutableSequence
from dataclasses import dataclass, field

from gofra.lexer import Token

from .exceptions import ParserEmptyInputTokensError
from .macros import Macro
from .operators import Operator, OperatorOperand, OperatorType


@dataclass(frozen=False)
class ParserContext:
    """Context for parsing which only required from internal usages."""

    tokens: deque[Token]
    operators: MutableSequence[Operator] = field(default_factory=list)
    macros: MutableMapping[str, Macro] = field(default_factory=dict)
    context_stack: deque[tuple[int, Operator]] = field(default_factory=deque)

    current_operator: int = field(default=0)

    def __post_init__(self) -> None:
        if not self.tokens:
            raise ParserEmptyInputTokensError

    def tokens_exhausted(self) -> bool:
        return len(self.tokens) == 0

    def has_context_stack(self) -> bool:
        return len(self.context_stack) > 0

    def new_macro(self, from_token: Token, name: str) -> Macro:
        macro = Macro(location=from_token.location, inner_tokens=[], name=name)
        self.macros[name] = macro
        return macro

    def expand_from_macro(self, macro: Macro) -> None:
        self.tokens.extend(deque(reversed(macro.inner_tokens)))

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
