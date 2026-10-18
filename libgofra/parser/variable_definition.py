from libgofra.hir.variable import Variable, VariableScopeClass, VariableStorageClass
from libgofra.lexer.keywords import Keyword
from libgofra.lexer.tokens import Token, TokenType
from libgofra.parser._context import ParserScope
from libgofra.parser.errors.constant_variable_requires_initializer import (
    ConstantVariableRequiresInitializerError,
)
from libgofra.parser.errors.general_name_conflict_error import (
    GeneralNameHolderConflictError,
)
from libgofra.parser.errors.wildcard_cannot_be_used_as_symbol_name import (
    WildcardCannotBeUsedAsSymbolNameError,
)
from libgofra.parser.exceptions import ParserVariableNameAlreadyDefinedAsVariableError
from libgofra.parser.literals import parse_any_literal
from libgofra.parser.type_parser import (
    parse_concrete_type_from_tokenizer,
)
from libgofra.typecheck.inference import infer_type_from_literal


def _consume_variable_modifier_is_const(
    context: ParserScope,
    begin_token: Token,
) -> bool:
    """Consume modifiers for *definition* (e.g constant or variable* from token that describes start of definition (any modifier or specifier).

    Next token must be an identifier holding definition name.

    Allowed forms: `const x`, `const var x`, `var x`
    """
    assert begin_token.type == TokenType.KEYWORD, "Expected keyword (e.g const / var)"

    if begin_token.value != Keyword.CONST_DEFINE:
        return False

    peeked = context.peek_token()
    if peeked.type == TokenType.KEYWORD and peeked.value == Keyword.VARIABLE_DEFINE:
        context.advance_token()
        # Skip `var` token, if next is non an identifier - caller must emit an error by itself

    return True


def _validate_variable_name_redefinition(
    context: ParserScope,
    name: str,
    token: Token,
) -> None:
    if name in context.variables:
        raise ParserVariableNameAlreadyDefinedAsVariableError(
            token=token,
            name=name,
        )

    if name == "_":
        raise WildcardCannotBeUsedAsSymbolNameError(at=token.location)

    if name_holder := context.query_name_holder(name):
        raise GeneralNameHolderConflictError(
            name_holder=name_holder,
            conflicting_holder=f"Variable '{name}' at {token.location}",
        )


def unpack_variable_definition_from_token(
    context: ParserScope,
    token: Token,
) -> None:
    assert context.module
    assert token.type == TokenType.KEYWORD
    modifier_is_const = _consume_variable_modifier_is_const(context, token)

    context.expect_token(TokenType.IDENTIFIER)
    token = context.next_token()

    name = token.text
    _validate_variable_name_redefinition(context, name, token)

    storage_class = (
        VariableStorageClass.STATIC
        if context.is_top_level
        else VariableStorageClass.STACK
    )
    scope_class = (
        VariableScopeClass.GLOBAL
        if context.is_top_level
        else VariableScopeClass.FUNCTION
    )

    var_t = None
    if context.peek_token().type != TokenType.ASSIGNMENT:
        var_t = parse_concrete_type_from_tokenizer(context)

    initial_value = None

    if context.peek_token().type == TokenType.ASSIGNMENT:
        context.advance_token()  # consume =
        initial_value = parse_any_literal(context)

    # Inference
    if var_t is None:
        if initial_value is None:
            msg = "Empty variable definition"
            raise ValueError(msg)
        var_t = infer_type_from_literal(initial_value, module=context.module)

    if modifier_is_const and initial_value is None:
        raise ConstantVariableRequiresInitializerError(name, token.location)

    context.variables[name] = Variable(
        name=name,
        module=context.module,
        defined_at=token.location,
        type=var_t,
        scope_class=scope_class,
        storage_class=storage_class,
        initial_value=initial_value,
        is_constant=modifier_is_const,
    )
