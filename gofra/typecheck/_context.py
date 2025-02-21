from collections.abc import MutableSequence
from dataclasses import dataclass

from gofra.parser.operators import Operator

from .exceptions import (
    TypecheckInvalidArgumentTypeError,
    TypecheckNotEnoughArgumentsError,
)
from .types import GofraType


@dataclass(frozen=False)
class TypecheckContext:
    """Context for type checking which only required from internal usages."""

    operators: MutableSequence[Operator]

    emulated_stack_types: MutableSequence[GofraType]

    def push_types(self, *types: GofraType) -> None:
        self.emulated_stack_types.extend(types)

    def raise_for_enough_arguments(
        self,
        operator: Operator,
        required_args: int,
    ) -> None:
        stack_size = len(self.emulated_stack_types)
        if stack_size < required_args:
            raise TypecheckNotEnoughArgumentsError(
                operator=operator,
                types_on_stack=self.emulated_stack_types,
                required_args=required_args,
            )

    def pop_argument_type(self) -> GofraType:
        return self.emulated_stack_types.pop()

    def pop_and_raise_for_argument_type(
        self,
        expected_type: GofraType,
        operator: Operator,
    ) -> GofraType:
        arg_type = self.pop_argument_type()
        if arg_type != expected_type:
            raise TypecheckInvalidArgumentTypeError(
                expected_type=expected_type,
                actual_type=arg_type,
                operator=operator,
            )
        return arg_type

    def consume_n_arguments(self, args_to_consume: int) -> None:
        for _ in range(args_to_consume):
            self.pop_argument_type()
