from collections import deque
from collections.abc import Sequence

from gofra.parser import Operator, OperatorType
from gofra.parser.intrinsics import Intrinsic

from ._context import TypecheckContext
from .exceptions import (
    TypecheckNonEmptyStackAtEndError,
)
from .types import GofraType


def validate_type_safety(operators: Sequence[Operator]) -> None:
    context = TypecheckContext(operators=deque(operators), emulated_stack_types=[])

    for operator in operators:
        match operator.type:
            case OperatorType.WHILE | OperatorType.END:
                ...
            case OperatorType.PUSH_INTEGER:
                push_type = GofraType.INTEGER

                if (
                    operator.has_optimizations
                    and operator.infer_type_after_optimization
                ):
                    push_type = operator.infer_type_after_optimization

                context.push_types(push_type)
            case OperatorType.PUSH_STRING:
                context.push_types(GofraType.POINTER, GofraType.INTEGER)
            case OperatorType.INTRINSIC:
                assert isinstance(operator.operand, Intrinsic)
                match operator.operand:
                    case Intrinsic.MEMORY_POINTER:
                        context.push_types(GofraType.POINTER)
                    case Intrinsic.MEMORY_WRITE:
                        context.raise_for_enough_arguments(operator, required_args=2)
                        context.pop_and_raise_for_argument_type(
                            GofraType.POINTER,
                            operator=operator,
                        )
                        context.pop_argument_type()
                    case Intrinsic.MEMORY_READ:
                        context.raise_for_enough_arguments(operator, required_args=2)
                        context.pop_and_raise_for_argument_type(
                            GofraType.POINTER,
                            operator=operator,
                        )
                        context.push_types(GofraType.INTEGER)
                    case Intrinsic.INCREMENT | Intrinsic.DECREMENT:
                        context.raise_for_enough_arguments(operator, required_args=1)
                        context.push_types(
                            context.pop_and_raise_for_argument_type(
                                GofraType.INTEGER,
                                operator=operator,
                            ),
                        )
                    case Intrinsic.DROP:
                        context.raise_for_enough_arguments(operator, required_args=1)
                        context.consume_n_arguments(args_to_consume=1)
                    case (
                        Intrinsic.EQUAL
                        | Intrinsic.LESS_EQUAL_THAN
                        | Intrinsic.LESS_THAN
                        | Intrinsic.GREATER_EQUAL_THAN
                        | Intrinsic.GREATER_THAN
                        | Intrinsic.NOT_EQUAL
                    ):
                        context.raise_for_enough_arguments(operator, required_args=2)
                        context.consume_n_arguments(args_to_consume=2)
                        context.push_types(GofraType.BOOLEAN)
                    case (
                        Intrinsic.MINUS
                        | Intrinsic.PLUS
                        | Intrinsic.MULTIPLY
                        | Intrinsic.DIVIDE
                        | Intrinsic.MODULUS
                    ):
                        context.raise_for_enough_arguments(operator, required_args=2)
                        context.consume_n_arguments(args_to_consume=2)
                        context.push_types(GofraType.INTEGER)
                    case (
                        Intrinsic.SYSCALL0
                        | Intrinsic.SYSCALL1
                        | Intrinsic.SYSCALL2
                        | Intrinsic.SYSCALL3
                        | Intrinsic.SYSCALL4
                        | Intrinsic.SYSCALL5
                        | Intrinsic.SYSCALL6
                    ):
                        args_count = operator.get_syscall_arguments_count()

                        injected_args = operator.syscall_optimization_injected_args
                        if injected_args:
                            types = [
                                GofraType.INTEGER
                                for injected_arg_value in injected_args
                                if injected_arg_value is not None
                            ]
                            context.push_types(*types)
                        context.raise_for_enough_arguments(operator, args_count)
                        context.consume_n_arguments(args_count)

                        if not operator.syscall_optimization_omit_result:
                            context.push_types(GofraType.INTEGER)
                    case Intrinsic.COPY:
                        context.raise_for_enough_arguments(operator, required_args=1)

                        arg_type = context.pop_argument_type()
                        context.push_types(arg_type, arg_type)
                    case Intrinsic.SWAP:
                        context.raise_for_enough_arguments(operator, required_args=1)

                        a = context.pop_argument_type()
                        b = context.pop_argument_type()

                        context.push_types(a, b)
            case OperatorType.IF:
                context.raise_for_enough_arguments(operator, required_args=1)
                context.pop_and_raise_for_argument_type(
                    GofraType.BOOLEAN,
                    operator=operator,
                )
            case OperatorType.DO:
                context.raise_for_enough_arguments(operator, required_args=1)
                context.pop_and_raise_for_argument_type(
                    GofraType.BOOLEAN,
                    operator=operator,
                )

    if context.emulated_stack_types:
        raise TypecheckNonEmptyStackAtEndError(
            stack_size=len(context.emulated_stack_types),
        )
