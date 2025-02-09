import operator as python_operator
from typing import Callable, assert_never

from gofra.lexer import Token, TokenType
from gofra.parser import Operator, OperatorType
from gofra.parser.intrinsics import Intrinsic

type FoldPredicate = Callable[[int, int], int]


def optimize_constant_folding(unoptimized_operators: list[Operator]):
    operators: list[Operator] = unoptimized_operators[:2]

    idx = 2
    idx_end = len(unoptimized_operators)

    while idx < idx_end:
        operator = unoptimized_operators[idx]
        idx += 1

        if operator.type != OperatorType.INTRINSIC:
            operators.append(operator)
            continue

        assert isinstance(operator.operand, Intrinsic)
        fold_predicate: FoldPredicate | None = None
        match operator.operand:
            case Intrinsic.PLUS:
                fold_predicate = python_operator.add
            case Intrinsic.MINUS:
                fold_predicate = python_operator.sub
            case Intrinsic.MULTIPLY:
                fold_predicate = python_operator.mul
            case Intrinsic.DIVIDE:
                fold_predicate = python_operator.truediv
            case Intrinsic.MODULUS:
                fold_predicate = python_operator.mod
            case Intrinsic.EQUAL:
                fold_predicate = python_operator.eq
            case Intrinsic.NOT_EQUAL:
                fold_predicate = python_operator.ne
            case Intrinsic.LESS_THAN:
                fold_predicate = python_operator.lt
            case Intrinsic.GREATER_THAN:
                fold_predicate = python_operator.gt
            case Intrinsic.LESS_EQUAL_THAN:
                fold_predicate = python_operator.le
            case Intrinsic.GREATER_EQUAL_THAN:
                fold_predicate = python_operator.ge
            case (
                Intrinsic.INCREMENT
                | Intrinsic.DECREMENT
                | Intrinsic.COPY
                | Intrinsic.COPY2
                | Intrinsic.FREE
                | Intrinsic.SWAP
                | Intrinsic.COPY_OVER
                | Intrinsic.SYSCALL2
                | Intrinsic.SYSCALL4
                | Intrinsic.SYSCALL5
                | Intrinsic.SWAP_OVER
                | Intrinsic.SYSCALL7
            ):
                ...
            case _:
                assert_never(operator.operand)
        if fold_predicate:
            was_folded = _fold_binary_integer_math_operator(
                idx,
                operators,
                unoptimized_operators,
                fold_predicate=fold_predicate,
            )
            if was_folded:
                continue

        operators.append(operator)
    return operators


def _fold_binary_integer_math_operator(
    idx: int,
    operators: list[Operator],
    unoptimized_operators: list[Operator],
    *,
    fold_predicate: FoldPredicate,
) -> bool:
    assert idx > 2
    operands = [
        unoptimized_operators[idx - 2],
        unoptimized_operators[idx - 3],
    ]
    if not (operands[0].type == operands[1].type == OperatorType.PUSH_INTEGER):
        return False

    operands = [operands[0].operand, operands[1].operand]
    assert isinstance(operands[0], int) and isinstance(operands[1], int)

    # TODO(@kirillzhosul): Folded predicate is weird for floating point math that is converted
    # while using integer math
    folded_value = int(fold_predicate(operands[0], operands[1]))

    operators.pop()
    operators.pop()

    # TODO(@kirillzhosul): Not unfolded to previous operator as previous one may be folded with new one
    operator = Operator(
        type=OperatorType.PUSH_INTEGER,
        token=Token(
            type=TokenType.INTEGER,
            text="__optimized__",
            value=folded_value,
            location=(unoptimized_operators[0].token.location[0], -1, -1),
        ),
        operand=folded_value,
        has_optimizations=True,
    )

    operators.append(operator)
    return True
