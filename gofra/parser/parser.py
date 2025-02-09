from typing import assert_never

from gofra.lexer import Keyword, Token, TokenType

from .exceptions import (
    ParserContextNotClosedError,
    ParserElseAfterNonIfError,
    ParserEmptyInputTokensError,
    ParserEndAfterWhileError,
    ParserEndWithoutContextError,
    ParserError,
    ParserNoIfBeforeElseError,
    ParserNoWhileBeforeDoError,
    ParserUnknownWordError,
)
from .intrinsics import WORD_TO_INTRINSIC
from .operators import Operator, OperatorType

type Operators = list[Operator]


def parse_tokens(tokens: list[Token]) -> list[Operator]:
    reversed_tokens = list(reversed(tokens))

    operator_idx = 0
    operators: list[Operator] = []
    context_stack: list[int] = []

    if not reversed_tokens:
        raise ParserEmptyInputTokensError

    while len(reversed_tokens) > 0:
        token = reversed_tokens.pop()
        match token.type:
            case TokenType.INTEGER:
                _push_integer_operator(operators, token)
            case TokenType.FLOAT:
                _push_float_operator(operators, token)
            case TokenType.SYMBOL:
                _push_symbol_operator(operators, token)
            case TokenType.WORD:
                _push_intrinsic_operator_from_word(operators, token)
            case TokenType.KEYWORD:
                assert isinstance(token.value, Keyword)
                match token.value:
                    case Keyword.IF:
                        operator = Operator(
                            type=OperatorType.IF,
                            token=token,
                            operand=None,
                        )
                        operators.append(operator)
                        context_stack.append(operator_idx)
                    case Keyword.DO:
                        if not context_stack:
                            raise ParserNoWhileBeforeDoError

                        # Get `WHILE` operator from context
                        anchor_operator_idx = context_stack.pop()
                        context_operator = operators[anchor_operator_idx]
                        if context_operator.type != OperatorType.WHILE:
                            raise ParserNoWhileBeforeDoError

                        operator = Operator(
                            type=OperatorType.DO,
                            token=token,
                            operand=None,
                        )
                        operators.append(operator)
                        context_stack.append(operator_idx)

                        # Cross-reference `WHILE` block to say where to jump in execution
                        operators[operator_idx].operand = anchor_operator_idx
                    case Keyword.WHILE:
                        operator = Operator(
                            type=OperatorType.WHILE,
                            token=token,
                            operand=None,
                        )
                        operators.append(operator)
                        context_stack.append(operator_idx)
                    case Keyword.ELSE:
                        if not context_stack:
                            raise ParserNoIfBeforeElseError

                        # Get `IF` operator from context.
                        anchor_operator_idx = context_stack.pop()
                        context_operator = operators[anchor_operator_idx]

                        if context_operator.type != OperatorType.IF:
                            raise ParserElseAfterNonIfError

                        operator = Operator(
                            type=OperatorType.ELSE,
                            token=token,
                            operand=None,
                        )
                        operators.append(operator)
                        context_stack.append(operator_idx)

                        # Cross-reference `IF` block to say where to jump in execution
                        # (jump inside `ELSE` block)
                        context_operator.operand = operator_idx + 1
                    case Keyword.END:
                        if not context_stack:
                            raise ParserEndWithoutContextError

                        # Get block (context) operator from context.
                        anchor_operator_idx = context_stack.pop()
                        context_operator = operators[anchor_operator_idx]

                        operator = Operator(
                            type=OperatorType.END,
                            token=token,
                            operand=None,
                        )
                        operators.append(operator)
                        match context_operator.type:
                            case OperatorType.IF:
                                # Cross-reference `IF` block to say where to jump in execution
                                # (jump after `END` block)
                                context_operator.operand = operator_idx + 1
                            case OperatorType.ELSE:
                                # Cross-reference `ELSE` block to say where to jump in execution
                                # (jump after `END` block)
                                context_operator.operand = operator_idx + 1
                            case OperatorType.DO:
                                assert context_operator.operand is not None
                                assert isinstance(context_operator.operand, int)

                                operators[
                                    operator_idx
                                ].operand = context_operator.operand
                                context_operator.operand = operator_idx + 1
                            case OperatorType.END:
                                raise ParserError
                            case OperatorType.WHILE:
                                raise ParserEndAfterWhileError
                            case _:
                                never = context_operator.type
                                if never in (
                                    OperatorType.PUSH_FLOAT,
                                    OperatorType.PUSH_INTEGER,
                                    OperatorType.PUSH_SYMBOL,
                                    OperatorType.PUSH_STRING,
                                    OperatorType.INTRINSIC,
                                ):
                                    raise ParserError
                                assert_never(never)
                    case _:
                        assert_never(token.value)
            case TokenType.STRING:
                _push_string_operator(operators, token)
            case _:
                assert_never(token.type)
        operator_idx += 1

    if context_stack:
        raise ParserContextNotClosedError

    return operators


def _push_string_operator(operators: Operators, token: Token) -> None:
    assert isinstance(token.value, str)
    operator = Operator(
        type=OperatorType.PUSH_STRING,
        token=token,
        operand=token.value,
    )
    operators.append(operator)


def _push_integer_operator(operators: Operators, token: Token) -> None:
    assert isinstance(token.value, int)
    operator = Operator(
        type=OperatorType.PUSH_INTEGER,
        token=token,
        operand=token.value,
    )
    operators.append(operator)


def _push_float_operator(operators: Operators, token: Token) -> None:
    assert isinstance(token.value, float)
    operator = Operator(
        type=OperatorType.PUSH_FLOAT,
        token=token,
        operand=token.value,
    )
    operators.append(operator)


def _push_symbol_operator(operators: Operators, token: Token) -> None:
    assert isinstance(token.value, str)
    operator = Operator(
        type=OperatorType.PUSH_SYMBOL,
        token=token,
        operand=token.value,
    )
    operators.append(operator)


def _push_intrinsic_operator_from_word(operators: Operators, token: Token) -> None:
    assert isinstance(token.value, str)
    intrinsic = WORD_TO_INTRINSIC.get(token.value)
    if intrinsic is None:
        raise ParserUnknownWordError(token=token)
    operator = Operator(
        type=OperatorType.INTRINSIC,
        token=token,
        operand=intrinsic,
    )
    operators.append(operator)
