from libgofra.hir.operator import OperatorType
from libgofra.lexer import Token, TokenType
from libgofra.parser._context import ParserContext


def parse_inline_assembly_intrinsic(scope: ParserContext, token: Token) -> None:
    scope.expect_token(TokenType.STRING)
    asm_source = scope.next_token()
    assert isinstance(asm_source.value, str)
    scope.push_new_operator(
        OperatorType.INLINE_RAW_ASM,
        token=token,
        operand=asm_source.value,
        is_contextual=False,
    )
