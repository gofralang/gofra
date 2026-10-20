from libgofra.hir.operator import OperatorType
from libgofra.lexer import Token
from libgofra.parser._context import ParserContext
from libgofra.parser.type_parser import parse_concrete_type_from_tokenizer


def parse_align_of_intrinsic(context: ParserContext, token: Token) -> None:
    alignment_of_type = parse_concrete_type_from_tokenizer(
        context,
        allow_inferring_variable_types=False,  # ? must be
    )

    context.push_new_operator(
        OperatorType.PUSH_INTEGER,
        token=token,
        operand=alignment_of_type.alignment,
    )
