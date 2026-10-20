from libgofra.lexer.tokens import TokenType
from libgofra.parser._context import ParserContext
from libgofra.parser.errors.type_definition_already_exists import (
    TypeDefinitionAlreadyExistsError,
)
from libgofra.parser.errors.wildcard_cannot_be_used_as_symbol_name import (
    WildcardCannotBeUsedAsSymbolNameError,
)
from libgofra.parser.type_parser import (
    consume_generic_type_parameters,
    parse_generic_type_alias_from_tokenizer,
)


def parse_type_declaration(context: ParserContext) -> None:
    name_token = context.next_token()

    if name_token.type != TokenType.IDENTIFIER:
        msg = f"Expected type declaration name at {name_token.location} to be an identifier but got {name_token.type.name}"
        raise ValueError(msg)

    typename = name_token.text

    if typename == "_":
        raise WildcardCannotBeUsedAsSymbolNameError(name_token.location)

    if context.scope.lookup(typename):
        raise TypeDefinitionAlreadyExistsError(typename, name_token.location)
    generic_type_params = consume_generic_type_parameters(context)
    context.scope.declare_type(
        typename,
        parse_generic_type_alias_from_tokenizer(
            context,
            generic_type_params=generic_type_params,
        ),
    )
