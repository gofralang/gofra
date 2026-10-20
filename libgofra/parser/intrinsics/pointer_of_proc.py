from libgofra.hir.function import Function
from libgofra.hir.operator import FunctionCallOperand, OperatorType
from libgofra.lexer import Token, TokenType
from libgofra.parser._context import ParserContext


def parse_pointer_of_proc_intrinsic(context: ParserContext, token: Token) -> None:
    function_name_token = context.next_token()
    if function_name_token.type != TokenType.IDENTIFIER:
        msg = f"Expected identifier as function name for pointer-of-proc at {token.location} but got {function_name_token.type}"
        raise ValueError(msg)

    function_name = function_name_token.text
    function = context.scope.lookup(function_name)
    if not isinstance(function, Function):
        msg = "pointer of proc for not a function!"
        raise ValueError(msg)  # noqa: TRY004

    context.push_new_operator(
        OperatorType.PUSH_FUNCTION_POINTER,
        token=token,
        operand=FunctionCallOperand(None, function),
    )
