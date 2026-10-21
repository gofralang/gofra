from dataclasses import dataclass

from libgofra.hir.literals import Literal_T
from libgofra.hir.variable import Variable, VariableScopeClass, VariableStorageClass
from libgofra.lexer.keywords import Keyword
from libgofra.lexer.tokens import Token, TokenType
from libgofra.parser._context import ParserContext
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
from libgofra.types import Type
from libgofra.types.inference import infer_type_from_literal

# TODO: attributes for variable definitions


@dataclass
class _VariableSpec:
    is_const: bool
    name: str
    token: Token
    explicit_type: Type | None


def parse_variable_definition(
    scope: ParserContext,
    token: Token,
) -> None:
    """Parse and define variable starting from type specifier keyword."""
    spec = _parse_variable_spec(scope, token)
    _validate_variable_name_redefinition(scope, spec.name, token)

    initializer = _parse_variable_initializer(scope, spec)
    type = _infer_variable_type(scope, spec, initializer)  # noqa: A001

    _define_variable(scope, spec, type, initializer)


def _infer_variable_type(  # noqa: ANN202
    scope: ParserContext,
    spec: _VariableSpec,
    initializer: Literal_T | None,
):
    if spec.explicit_type:
        return spec.explicit_type

    assert scope.module
    assert initializer is not None
    return infer_type_from_literal(initializer, types=scope.module.types)


def _define_variable(
    context: ParserContext,
    spec: _VariableSpec,
    type: Type,  # noqa: A002
    initializer: Literal_T | None,
) -> None:

    storage_class = (
        VariableStorageClass.STATIC
        if context.scope.is_global
        else VariableStorageClass.STACK
    )
    scope_class = (
        VariableScopeClass.GLOBAL
        if context.scope.is_global
        else VariableScopeClass.FUNCTION
    )
    context.scope.declare_variable(
        spec.name,
        Variable(
            name=spec.name,
            module=context.module,
            defined_at=spec.token.location,
            type=type,
            scope_class=scope_class,
            storage_class=storage_class,
            initial_value=initializer,
            is_constant=spec.is_const,
        ),
    )


def _parse_variable_initializer(
    context: ParserContext,
    spec: _VariableSpec,
) -> Literal_T | None:
    if context.peek_token().type == TokenType.ASSIGNMENT:
        context.advance_token()  # consume =
        return parse_any_literal(context)

    if spec.is_const:
        raise ConstantVariableRequiresInitializerError(
            spec.name,
            context.peek_token().location,
        )

    return None


def _validate_variable_name_redefinition(
    context: ParserContext,
    name: str,
    token: Token,
) -> None:
    if name in context.scope.variables:
        raise ParserVariableNameAlreadyDefinedAsVariableError(
            token=token,
            name=name,
        )

    if name == "_":
        raise WildcardCannotBeUsedAsSymbolNameError(at=token.location)

    if name_holder := context.scope.lookup(name):
        raise GeneralNameHolderConflictError(
            name_holder=name_holder,
            conflicting_holder=f"Variable '{name}' at {token.location}",
        )


def _parse_variable_spec(
    scope: ParserContext,
    modifier_token: Token,
) -> _VariableSpec:
    assert modifier_token.type == TokenType.KEYWORD and modifier_token.value in (  # noqa: PT018
        Keyword.CONST_DEFINE,
        Keyword.VARIABLE_DEFINE,
    ), "Expected keyword (CONST_DEFINE / VARIABLE_DEFINE modifier)"

    scope.expect_token(TokenType.IDENTIFIER)
    name_token = scope.next_token()

    explicit_type = (
        parse_concrete_type_from_tokenizer(scope)
        if scope.peek_token().type != TokenType.ASSIGNMENT
        else None
    )

    return _VariableSpec(
        name=name_token.text,
        token=name_token,
        explicit_type=explicit_type,
        is_const=modifier_token.value == Keyword.CONST_DEFINE,
    )
