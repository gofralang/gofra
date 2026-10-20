from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from libgofra.hir.operator import (
    FunctionCallOperand,
    Operator,
    OperatorType,
    StructAccessor,
)
from libgofra.lexer import Token
from libgofra.parser.errors.general_expect_token import ExpectedTokenByParserError

if TYPE_CHECKING:
    from collections.abc import (
        Callable,
        Generator,
        MutableSequence,
    )
    from pathlib import Path

    from libgofra.hir.function import Function
    from libgofra.hir.module import Module
    from libgofra.lexer.tokens import TokenType
    from libgofra.parser.scope import Scope
    from libgofra.parser.statements.control_flow import RangeQualifier
    from libgofra.types._base import Type


@dataclass
class TokenStream:
    _tokenizer: Generator[Token] = field()
    _peeked: deque[Token] = field(default_factory=deque[Token], init=False)

    def next(self) -> Token:
        if self._peeked:
            return self._peeked.popleft()
        return next(self._tokenizer)

    def advance(self) -> None:
        self.next()

    def peek(self, n: int = 0) -> Token:
        while len(self._peeked) <= n:
            self._peeked.append(next(self._tokenizer))
        return self._peeked[n]

    def push_back_upfront_peeked(self, token: Token) -> None:
        """Push token in front of peeked ones, so next/peek will take it last in order of peeked."""
        self._peeked.appendleft(token)


@dataclass(frozen=False)
class ParserContext:
    """Context for parsing which only required from internal usages."""

    tokens: TokenStream
    scope: Scope
    module: Module

    # Will be called when scope encounters import request
    # goal of this callback to load specified named import and inject as dependency
    # both scope and parser itself is not responsible for loading near modules
    on_import_request: Callable[[str, Path], None] = field(repr=False, kw_only=True)

    # Resulting operators from parsing
    operators: MutableSequence[Operator] = field(default_factory=list[Operator])

    context_stack: deque[tuple[int, Operator, RangeQualifier | None]] = field(
        default_factory=deque[tuple[int, Operator, "RangeQualifier | None"]],
    )

    entry_point_name: str = "main"

    # Runtime arrays Out-Of-Bounds check
    rt_array_oob_check: bool = field(default=False)

    # No function calls in that context
    # Maybe should be refactored
    is_leaf_context: bool = field(default=True)

    @property
    def path(self) -> Path:
        assert self.module
        return self.module.path

    def next_token(self) -> Token:
        return self.tokens.next()

    def advance_token(self) -> None:
        return self.tokens.advance()

    def peek_token(self, n: int = 0) -> Token:
        return self.tokens.peek(n)

    def expect_token(self, type: TokenType | tuple[TokenType, ...]) -> None:  # noqa: A002
        token = self.peek_token()
        if not isinstance(type, tuple):
            type = (type,)  # noqa: A001

        # TODO: proper error
        if token.type not in type:
            raise ExpectedTokenByParserError(expected=type[0], got=token)

    def push_token_back_upfront_peeked(self, token: Token) -> None:
        """Push token in front of peeked ones, so next/peek will take it last in order of peeked."""
        return self.tokens.push_back_upfront_peeked(token)

    def has_context_stack(self) -> bool:
        return len(self.context_stack) > 0

    @property
    def current_operator(self) -> int:
        return len(self.operators)

    def expand_from_inline_block(self, inline_block: Function) -> None:
        if inline_block.attrs.external:
            msg = "Cannot expand extern function."
            raise ValueError(msg)
        if any(op.type == OperatorType.FUNCTION_CALL for op in inline_block.operators):
            self.is_leaf_context = False

        self.operators.extend(inline_block.operators)

    def pop_context_stack(self) -> tuple[int, Operator, RangeQualifier | None]:
        return self.context_stack.pop()

    def push_new_operator(
        self,
        type: OperatorType,  # noqa: A002
        token: Token,
        operand: float
        | str
        | Type
        | StructAccessor
        | FunctionCallOperand
        | None = None,
        *,
        is_contextual: bool = False,
    ) -> None:
        """:param is_contextual: push onto context stack to backpatch later."""
        if type == OperatorType.FUNCTION_CALL:
            self.is_leaf_context = False

        operator = Operator(
            type=type,
            token=token,
            operand=operand,
        )
        self.operators.append(operator)
        if is_contextual:
            self.context_stack.append((self.current_operator - 1, operator, None))

    def finalize(self) -> None:
        self.module.functions.update(self.scope.functions)
        self.module.variables.update(self.scope.variables)
        self.module.types.update(self.scope.types)

        self.module.entry_point_ref = self.scope.functions.get(
            self.entry_point_name,
            None,
        )
