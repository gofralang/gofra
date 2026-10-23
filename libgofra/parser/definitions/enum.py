from libgofra.hir.operator import OperatorType
from libgofra.lexer.keywords import Keyword
from libgofra.lexer.tokens import TokenType
from libgofra.parser._context import ParserContext
from libgofra.parser.errors.wildcard_cannot_be_used_as_symbol_name import (
    WildcardCannotBeUsedAsSymbolNameError,
)
from libgofra.types.primitive.enums import EnumType
from libgofra.types.primitive.integers import I64Type


def parse_enum_definition(context: ParserContext) -> None:
    """Parse and define an enum type."""
    context.expect_token(TokenType.IDENTIFIER)
    name_token = context.next_token()

    if name_token.text == "_":
        raise WildcardCannotBeUsedAsSymbolNameError(at=name_token.location)

    if context.scope.lookup(name_token.text) is not None:
        msg = f"Enum {name_token.text} at {name_token.location} is already defined"
        raise ValueError(msg)

    # Enum is always i64; underlying types are intentionally not supported.
    underlying_type = I64Type()

    # Collect variants.
    variants: dict[str, int] = {}
    current_value = 0

    while True:
        token = context.next_token()
        if token.type == TokenType.KEYWORD and token.value == Keyword.END:
            break

        if token.type != TokenType.IDENTIFIER:
            msg = f"Expected enum variant name at {token.location} but got {token.type.name}"
            raise ValueError(msg)

        variant_name = token.text
        if variant_name == "_":
            raise WildcardCannotBeUsedAsSymbolNameError(at=token.location)

        # Optional explicit value.
        peeked_value = context.peek_token()
        if peeked_value.type == TokenType.ASSIGNMENT:
            context.advance_token()
            current_value = _parse_enum_value(context)
        elif peeked_value.type == TokenType.INTEGER:
            value_token = context.next_token()
            assert isinstance(value_token.value, int)
            current_value = value_token.value
        elif peeked_value.type == TokenType.IDENTIFIER:
            held = context.scope.lookup(peeked_value.text)
            if held is not None and getattr(held, "is_constant", False):
                initial_value = getattr(held, "initial_value", None)
                if initial_value is not None and hasattr(initial_value, "value"):
                    context.advance_token()
                    current_value = initial_value.value

        variants[variant_name] = current_value
        current_value += 1

    if not variants:
        msg = f"Enum {name_token.text} at {name_token.location} has no variants"
        raise ValueError(msg)

    enum_type = EnumType(
        name=name_token.text,
        underlying_type=underlying_type,
        variants=variants,
    )
    context.scope.declare_type(name_token.text, enum_type)


def try_parse_enum_variant_accessor_expr(
    context: ParserContext,
    token: object,
) -> bool:
    # Accept either a Token-like object or a token text carrier.
    token_text = getattr(token, "text", None)
    if not isinstance(token_text, str):
        return False

    holder = context.scope.lookup(token_text)
    if not isinstance(holder, EnumType):
        return False

    # Need at least EnumName.Variant form.
    if context.peek_token().type != TokenType.DOT:
        return False

    context.advance_token()  # consume DOT
    variant_token = context.next_token()
    if variant_token.type != TokenType.IDENTIFIER:
        msg = f"Expected enum variant name at {variant_token.location}"
        raise ValueError(msg)

    if variant_token.text not in holder.variants:
        msg = f"Unknown enum variant {variant_token.text} for {holder.name} at {variant_token.location}"
        raise ValueError(msg)

    context.push_new_operator(
        type=OperatorType.PUSH_INTEGER,
        token=variant_token,
        operand=holder.variants[variant_token.text],
    )
    return True


def _parse_enum_value(context: ParserContext) -> int:
    if context.peek_token().type == TokenType.INTEGER:
        value_token = context.next_token()
        assert isinstance(value_token.value, int)
        return value_token.value

    if context.peek_token().type == TokenType.IDENTIFIER:
        held = context.scope.lookup(context.peek_token().text)
        if held is not None and getattr(held, "is_constant", False):
            initial_value = getattr(held, "initial_value", None)
            if initial_value is not None and hasattr(initial_value, "value"):
                value_token = context.next_token()
                return initial_value.value

    msg = f"Expected integer value for enum at {context.peek_token().location}"
    raise ValueError(msg)
