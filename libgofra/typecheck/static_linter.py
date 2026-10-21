"""Static analysis* functions.

Emits warning if they succeed to find some possible errors and bad things
"""

from collections.abc import Callable

from libgofra.hir.function import Function
from libgofra.lexer.tokens import TokenLocation
from libgofra.types._base import Type
from libgofra.types.composite.pointer import PointerMemoryLocation, PointerType


def lint_stack_memory_retval(
    on_lint_warning: Callable[[str], None],
    function: Function,
    retval_t: Type,
) -> None:
    """Emit lint warning if returned type is an stack memory."""
    if not isinstance(retval_t, PointerType):
        return
    if retval_t.memory_location == PointerMemoryLocation.STACK:
        on_lint_warning(
            f"""Returning an pointer from function that has stack memory location inside function '{function.name}' defined at {function.defined_at}!""",
        )


def emit_no_return_attribute_propagation_warning(
    on_lint_warning: Callable[[str], None],
    function: Function,
) -> None:
    on_lint_warning(
        f"Function '{function.name}' defined at {function.defined_at} calls to no-return function inside no conditional blocks, consider propagate no-return attribute",
    )


def emit_unreachable_code_after_early_return_warning(
    on_lint_warning: Callable[[str], None],
    function: Function,
    return_at: TokenLocation,
    unreachable_at: TokenLocation,
) -> None:
    on_lint_warning(
        f"Function '{function.name}' has operators after early-return at {return_at}! This is unreachable code starting at {unreachable_at}!",
    )


def emit_unreachable_code_after_no_return_call_warning(
    on_lint_warning: Callable[[str], None],
    call_from: Function,
    call_at: TokenLocation,
    callee: Function,
    unreachable_at: TokenLocation,
) -> None:
    assert callee.attrs.no_return
    on_lint_warning(
        f"Function '{call_from.name}' has operators after calling no-return function '{callee.name}' at {call_at}! This is unreachable code starting at {unreachable_at}!",
    )

