from libgofra.hir.operator import OperatorType
from libgofra.lexer import Token, TokenType
from libgofra.parser._context import ParserContext
from libgofra.parser.type_parser import parse_concrete_type_from_tokenizer
from libgofra.types.composite import StructureType


def parse_offset_of_intrinsic(context: ParserContext, token: Token) -> None:
    struct_type = parse_concrete_type_from_tokenizer(
        context,
        allow_inferring_variable_types=True,
    )
    if not isinstance(struct_type, StructureType):
        msg = f"Expected structure type at {token.location} but got {struct_type}"
        raise TypeError(msg)

    field_token = context.next_token()
    if field_token.type != TokenType.IDENTIFIER:
        msg = f"Expected identifier as field selector for offset-of at {token.location} but got {field_token.type}"
        raise ValueError(msg)

    field_name = field_token.text
    if not struct_type.has_field(field_name):
        msg = (
            f"Field {field_name} does not belongs to {struct_type} at {token.location}"
        )
        # TODO: in this place, and other like this, for generic structures it is possible to pinpoint at original generic type (non concrete one)
        raise ValueError(msg)
    context.push_new_operator(
        OperatorType.PUSH_INTEGER,
        token=token,
        operand=struct_type.get_field_offset(field_name),
    )
