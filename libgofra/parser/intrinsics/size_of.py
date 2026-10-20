from libgofra.hir.operator import OperatorType
from libgofra.lexer import Token
from libgofra.parser._context import ParserContext
from libgofra.parser.type_parser import parse_concrete_type_from_tokenizer


def parse_size_of_intrinsic(scope: ParserContext, token: Token) -> None:
    type = parse_concrete_type_from_tokenizer(  # noqa: A001
        scope,
        allow_inferring_variable_types=True,
    )
    scope.push_new_operator(
        OperatorType.PUSH_INTEGER,
        token=token,
        operand=type.size_in_bytes,
    )
