from collections.abc import MutableSequence
from dataclasses import dataclass

from gofra.parser.operators import Operator

from .exceptions import (
    TypecheckInvalidArgumentTypeError,
    TypecheckNotEnoughArgumentsError,
)
from .types import GofraType as T


@dataclass(frozen=False)
class TypecheckContext:
    """Context for type checking which only required for internal usages."""

    # Typechecker is an emulated type stack, e.g 1 2 would produce [INT, INT] ino type stack
    emulated_stack_types: MutableSequence[T]

    def push_types(self, *types: T) -> None:
        """Push given types onto emulated typeS stack."""
        self.emulated_stack_types.extend(types)

    def raise_for_enough_arguments(
        self,
        operator: Operator,
        required_args: int,
    ) -> None:
        """Expect that stack has N arguments."""
        stack_size = len(self.emulated_stack_types)
        if stack_size < required_args:
            raise TypecheckNotEnoughArgumentsError(
                operator=operator,
                types_on_stack=self.emulated_stack_types,
                required_args=required_args,
            )

    def pop_type_from_stack(self) -> T:
        """Pop current type on the stack."""
        return self.emulated_stack_types.pop()

    def consume_n_arguments(self, args_to_consume: int) -> None:
        """Pop N arguments from stack of any type."""
        for _ in range(args_to_consume):
            self.pop_type_from_stack()

    def raise_for_arguments(
        self,
        operator: Operator,
        *expected_types: T,
    ) -> None:
        """Expect given arguments and count and their types should match.

        Types are reversed so call will look like original stack.
        """
        assert expected_types, "Expected at least one type to expect"
        self.raise_for_enough_arguments(operator, len(expected_types))
        for expected_type in expected_types[::-1]:
            argument_type = self.pop_type_from_stack()
            if expected_type not in (T.ANY, argument_type):
                raise TypecheckInvalidArgumentTypeError(
                    expected_type=expected_type,
                    actual_type=argument_type,
                    operator=operator,
                )

    def _pop_and_raise_for_argument_type(
        self,
        expected_type: T,
        operator: Operator,
    ) -> T:
        arg_type = self.pop_type_from_stack()
        if arg_type != expected_type:
            raise TypecheckInvalidArgumentTypeError(
                expected_type=expected_type,
                actual_type=arg_type,
                operator=operator,
            )
        return arg_type
