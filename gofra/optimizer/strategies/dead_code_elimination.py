from gofra.context import ProgramContext
from gofra.parser.functions.function import Function
from gofra.parser.operators import OperatorType

DCE_MAX_TRAVERSIONS = 128


def optimize_dead_code_elimination(
    program: ProgramContext,
) -> None:
    """Remove dead code from final operators result."""
    dce_remove_unused_functions(program)


def dce_remove_unused_functions(program: ProgramContext) -> None:
    """Apply DCE for functions so unused functions are removed."""
    for _ in range(DCE_MAX_TRAVERSIONS):
        unused_functions = [
            function
            for function in program.functions.values()
            if not _is_function_was_called(program, program.functions[function.name])
        ]
        if not unused_functions:
            return

        [program.functions.pop(function.name) for function in unused_functions]


def _is_function_was_called(program: ProgramContext, function: Function) -> bool:
    """Check is given function was called atleast once in whole program."""
    for possible_caller in [*program.functions.values(), program.entry_point]:
        for operator in possible_caller.source:
            if (
                operator.type == OperatorType.FUNCTION_CALL
                and operator.operand == function.name
            ):
                return True
    return False
