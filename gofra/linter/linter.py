from typing import assert_never

from gofra.lexer import Token
from gofra.parser import Operator, OperatorType
from gofra.parser.intrinsics import Intrinsic

from .exceptions import (
    LinterAmbiguousStackAtEndError,
    LinterEmptyInputOperators,
    LinterPopFromEmptyStackError,
    LinterWrongTypecheckError,
)
from .types import LinterType


def linter_validate(operators: list[Operator]):
    if not operators:
        raise LinterEmptyInputOperators

    emulated_stack_types: list[tuple[LinterType, Token]] = []
    idx, idx_end = 0, len(operators)

    while idx < idx_end:
        operator = operators[idx]

        match operator.type:
            case OperatorType.PUSH_INTEGER | OperatorType.PUSH_SYMBOL:
                emulated_stack_types.append((LinterType.INTEGER, operator.token))
            case OperatorType.PUSH_FLOAT:
                raise NotImplementedError
            case OperatorType.PUSH_STRING:
                emulated_stack_types.append((LinterType.POINTER, operator.token))
                emulated_stack_types.append((LinterType.INTEGER, operator.token))
            case OperatorType.INTRINSIC:
                assert isinstance(operator.operand, Intrinsic)
                match operator.operand:
                    case Intrinsic.SYSCALL4:
                        stack_size = len(emulated_stack_types)
                        if stack_size < 4:
                            raise LinterPopFromEmptyStackError(
                                token=operator.token, underflow_size=4 - stack_size
                            )
                        emulated_stack_types.pop()
                        emulated_stack_types.pop()
                        emulated_stack_types.pop()
                        emulated_stack_types.pop()
                    case Intrinsic.SYSCALL5:
                        stack_size = len(emulated_stack_types)
                        if stack_size < 4:
                            raise LinterPopFromEmptyStackError(
                                token=operator.token, underflow_size=4 - stack_size
                            )
                        emulated_stack_types.pop()
                        emulated_stack_types.pop()
                        emulated_stack_types.pop()
                        emulated_stack_types.pop()
                        emulated_stack_types.pop()
                    case Intrinsic.SYSCALL2:
                        stack_size = len(emulated_stack_types)
                        if stack_size < 4:
                            raise LinterPopFromEmptyStackError(
                                token=operator.token, underflow_size=2 - stack_size
                            )
                        emulated_stack_types.pop()
                        emulated_stack_types.pop()
                    case Intrinsic.COPY:
                        stack_size = len(emulated_stack_types)
                        if stack_size < 1:
                            raise LinterPopFromEmptyStackError(
                                token=operator.token, underflow_size=1
                            )
                        emulated_stack_types.append(
                            (emulated_stack_types[-1][0], operator.token)
                        )
                    case Intrinsic.COPY2:
                        stack_size = len(emulated_stack_types)
                        if stack_size < 2:
                            raise LinterPopFromEmptyStackError(
                                token=operator.token, underflow_size=2 - stack_size
                            )
                        emulated_stack_types.append(
                            (emulated_stack_types[-1][0], operator.token)
                        )
                        emulated_stack_types.append(
                            (emulated_stack_types[-2][0], operator.token)
                        )
                    case Intrinsic.COPY_OVER:
                        stack_size = len(emulated_stack_types)
                        if stack_size < 2:
                            raise LinterPopFromEmptyStackError(
                                token=operator.token, underflow_size=2 - stack_size
                            )

                        emulated_stack_types.append(
                            (emulated_stack_types[-2][0], operator.token)
                        )
                    case Intrinsic.SWAP:
                        stack_size = len(emulated_stack_types)
                        if stack_size < 2:
                            raise LinterPopFromEmptyStackError(
                                token=operator.token, underflow_size=2 - stack_size
                            )

                        a = emulated_stack_types.pop()
                        b = emulated_stack_types.pop()

                        emulated_stack_types.append(a)
                        emulated_stack_types.append(b)

                    case Intrinsic.SWAP_OVER:
                        stack_size = len(emulated_stack_types)
                        if stack_size < 2:
                            raise LinterPopFromEmptyStackError(
                                token=operator.token, underflow_size=3 - stack_size
                            )

                        a = emulated_stack_types.pop()
                        b = emulated_stack_types.pop()
                        c = emulated_stack_types.pop()

                        emulated_stack_types.append(b)
                        emulated_stack_types.append(c)
                        emulated_stack_types.append(a)

                    case (
                        Intrinsic.MINUS
                        | Intrinsic.PLUS
                        | Intrinsic.MULTIPLY
                        | Intrinsic.DIVIDE
                        | Intrinsic.MODULUS
                    ):
                        stack_size = len(emulated_stack_types)
                        if stack_size < 2:
                            raise LinterPopFromEmptyStackError(
                                token=operator.token, underflow_size=2 - stack_size
                            )
                        emulated_stack_types.pop()
                        emulated_stack_types.pop()

                        emulated_stack_types.append(
                            (LinterType.INTEGER, operator.token)
                        )
                    case (
                        Intrinsic.EQUAL
                        | Intrinsic.LESS_EQUAL_THAN
                        | Intrinsic.LESS_THAN
                        | Intrinsic.GREATER_EQUAL_THAN
                        | Intrinsic.GREATER_THAN
                        | Intrinsic.NOT_EQUAL
                    ):
                        stack_size = len(emulated_stack_types)
                        if stack_size < 2:
                            raise LinterPopFromEmptyStackError(
                                token=operator.token, underflow_size=2 - stack_size
                            )
                        emulated_stack_types.pop()
                        emulated_stack_types.pop()

                        emulated_stack_types.append(
                            (LinterType.BOOLEAN, operator.token)
                        )
                    case Intrinsic.FREE:
                        emulated_stack_types.pop()
                    case Intrinsic.INCREMENT | Intrinsic.DECREMENT:
                        pass
                    case _:
                        assert_never(operator.operand)
            case OperatorType.WHILE:
                pass
            case OperatorType.IF:
                if len(emulated_stack_types) < 1:
                    raise LinterPopFromEmptyStackError(
                        underflow_size=1, token=operator.token
                    )
                operand = emulated_stack_types.pop()

                if operand != LinterType.BOOLEAN:
                    raise LinterWrongTypecheckError
            case OperatorType.DO:
                if len(emulated_stack_types) < 1:
                    raise LinterPopFromEmptyStackError(
                        underflow_size=1, token=operator.token
                    )
                operand = emulated_stack_types.pop()

                if operand != LinterType.BOOLEAN:
                    raise LinterWrongTypecheckError

                assert isinstance(operator.operand, int)
                end_block = operators[operator.operand]
                assert isinstance(end_block.operand, int)

                idx = end_block.operand
            case OperatorType.END | OperatorType.ELSE:
                assert isinstance(operator.operand, int)
                idx = operator.operand
            case _:
                assert_never(operator.type)
        idx += 1

    if emulated_stack_types:
        raise LinterAmbiguousStackAtEndError(token=emulated_stack_types[-1][1])
