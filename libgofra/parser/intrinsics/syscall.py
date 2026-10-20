from libgofra.hir.operator import OperatorType
from libgofra.lexer import Token
from libgofra.parser._context import ParserContext


def parse_syscall_intrinsic(scope: ParserContext, token: Token) -> None:
    scope.push_new_operator(
        token=token,
        type=OperatorType.SYSCALL,
        operand=int(token.text[-1]),
    )
