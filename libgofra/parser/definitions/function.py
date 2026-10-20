from collections.abc import Generator

from libgofra.hir.function import (
    Function,
    FunctionInlineAttribute,
    FunctionParameter,
    Visibility,
)
from libgofra.hir.operator import FunctionCallOperand, OperatorType
from libgofra.hir.variable import Variable, VariableScopeClass, VariableStorageClass
from libgofra.lexer import Keyword, Token, TokenType
from libgofra.lexer.keywords import KEYWORD_TO_NAME, WORD_TO_KEYWORD
from libgofra.lexer.tokens import TokenLocation
from libgofra.parser._context import ParserContext, TokenStream
from libgofra.parser.errors.general_name_conflict_error import (
    GeneralNameHolderConflictError,
)
from libgofra.parser.errors.lambda_with_extern_attr import LambdaWithExternAttrError
from libgofra.parser.errors.lambda_with_inline_attr import LambdaWithInlineAttrError
from libgofra.parser.errors.lambda_with_visibility_attr import (
    LambdaWithVisibilityAttrError,
)
from libgofra.parser.functions.parser import (
    FunctionHeaderDefinition,
    consume_function_definition,
)
from libgofra.parser.scope import Scope


def _declare_external_function(
    context: ParserContext,
    spec: FunctionHeaderDefinition,
    defined_at: TokenLocation,
) -> None:

    q = spec.qualifiers
    if q.is_inline or q.is_naked or q.is_no_mangle:
        msg = f"Prohibited combination of attributes for function at {defined_at}"
        raise ValueError(msg)

    function = Function.create_external(
        name=spec.name,
        defined_at=defined_at,
        parameters=spec.parameters,
        return_type=spec.return_type,
    )
    function.attrs.no_return = spec.qualifiers.is_no_return
    function.attrs.mangle = False
    function.module = context.module

    context.scope.declare_function(function)


def _validate_function_defintion_attributes(function: Function) -> None:
    # TODO: migrate into function attr parsing
    if function.attrs.inline:
        if function.attrs.recursive:
            msg = f"Inline functions cannot be recursive: {function.defined_at}"
            raise ValueError(msg)
        if function.variables:
            msg = f"Inline functions cannot have local variables: {function.defined_at}"
            raise ValueError(msg)
    if function.attrs.naked:
        if function.variables:
            msg = f"Naked functions cannot have local variables: {function.defined_at}"
            raise ValueError(msg)
        if not function.operators:
            msg = f"Instructions inside naked function: {function.defined_at}"
            raise ValueError(msg)
        for op in function.operators:
            if op.type != OperatorType.INLINE_RAW_ASM:
                msg = f"Naked functions can only have assembly inlined: {function.defined_at}"
                raise ValueError(msg)


def parse_function_definition(
    context: ParserContext,
    token: Token,
) -> None:
    f_header_def = consume_function_definition(context, token)

    # TODO: Generally bad function
    # references too many internal implementations


    if name_holder := context.scope.lookup(f_header_def.name):
        raise GeneralNameHolderConflictError(
            conflicting_holder=f"Function '{f_header_def.name}' at {token.location}",
            name_holder=name_holder,
        )

    if f_header_def.qualifiers.is_extern:
        return _declare_external_function(
            context,
            f_header_def,
            defined_at=token.location,
        )

    new_context = _new_function_scope(context, token, f_header_def.parameters)

    if f_header_def.name == context.entry_point_name:  # TODO: Refactor
        f_header_def.qualifiers.is_public = True
        f_header_def.qualifiers.is_no_mangle = True

    function = Function.create_internal(
        name=f_header_def.name,
        defined_at=token.location,
        operators=new_context.operators,
        variables=new_context.scope.variables,
        parameters=f_header_def.parameters,
        return_type=f_header_def.return_type,
    )

    function.attrs.leaf = new_context.is_leaf_context
    function.attrs.naked = f_header_def.qualifiers.is_naked
    function.attrs.mangle = not f_header_def.qualifiers.is_no_mangle
    function.attrs.inline = FunctionInlineAttribute.from_flag(
        f_header_def.qualifiers.is_inline,
    )

    if f_header_def.qualifiers.is_public:
        function.attrs.visibility = Visibility.PUBLIC

    function.attrs.no_return = f_header_def.qualifiers.is_no_return
    function.module = context.module

    _validate_function_defintion_attributes(function)
    enclosed_new_functions = [
        f
        for f in new_context.scope.functions.values()
        if f.name not in context.scope.functions
    ]

    if enclosed_new_functions:
        for enclosure in enclosed_new_functions:
            enclosure.outer_function = function
            _enclosure_generate_native_holder_name(
                context,
                owner=function,
                enclosure=enclosure,
            )
            context.scope.declare_function(enclosure)
    context.scope.declare_function(function)
    return None


def parse_lambda_function_definition(
    context: ParserContext,
    token: Token,
) -> None:
    assert token.type == TokenType.KEYWORD
    assert token.value == Keyword.LAMBDA_DEF
    assert not context.scope.is_global

    f_header_def = consume_function_definition(context, context.next_token())

    if f_header_def.qualifiers.is_extern:
        raise LambdaWithExternAttrError(at=token.location)

    if f_header_def.qualifiers.is_inline:
        raise LambdaWithInlineAttrError(at=token.location)

    if f_header_def.qualifiers.is_public:
        raise LambdaWithVisibilityAttrError(at=token.location)

    assert not f_header_def.qualifiers.is_no_mangle, "no-mangled lambda"

    # TODO(@kirillzhosul): doesn't anonymous functions do not hold their names?
    if context.scope.lookup(f_header_def.name):
        msg = f"Function name {f_header_def.name} is already taken by other definition"
        raise ValueError(msg)

    new_context = _new_function_scope(context, token, f_header_def.parameters)

    function = Function.create_internal(
        name=f_header_def.name,
        defined_at=token.location,
        operators=new_context.operators,
        variables=new_context.scope.variables,
        parameters=f_header_def.parameters,
        return_type=f_header_def.return_type,
    )
    function.attrs.mangle = False
    function.attrs.leaf = new_context.is_leaf_context
    function.attrs.naked = f_header_def.qualifiers.is_naked
    function.attrs.no_return = f_header_def.qualifiers.is_no_return

    function.attrs.visibility = Visibility.PRIVATE

    function.module = context.module
    assert not context.scope.is_global
    context.scope.declare_function(function)

    context.push_new_operator(
        OperatorType.PUSH_FUNCTION_POINTER,
        token=token,
        operand=FunctionCallOperand(None, function),
    )


def _new_function_scope(
    parent: ParserContext,
    token: Token,
    parameters: list[FunctionParameter],
) -> ParserContext:

    tokenizer = _consume_function_body_tokens(parent)

    new_scope = Scope(parent=parent.scope)
    new_context = ParserContext(
        module=parent.module,
        scope=new_scope,
        tokens=TokenStream(tokenizer),
        entry_point_name=parent.entry_point_name,  # TODO: Refactor
        on_import_request=parent.on_import_request,
    )

    for param in reversed(parameters):
        assert param.name
        if param.name == "_":
            new_context.push_new_operator(OperatorType.STACK_DROP, token=token)
            continue
        assert parent.module
        new_scope.variables[param.name] = Variable(
            module=parent.module,
            name=param.name,
            defined_at=token.location,
            is_constant=False,
            storage_class=VariableStorageClass.STACK,
            scope_class=VariableScopeClass.FUNCTION,
            type=param.type,
            initial_value=None,  # Default values propagated by caller
        )

        new_context.push_new_operator(
            OperatorType.LOAD_PARAM_ARGUMENT,
            token,
            operand=param.name,
        )
    from libgofra.parser.parser import (  # noqa: PLC0415
        _parse_from_context_into_operators,
    )

    _parse_from_context_into_operators(context=new_context)

    return new_context


def _enclosure_generate_native_holder_name(
    context: ParserContext,
    owner: Function,
    enclosure: Function,
) -> None:
    assert not enclosure.attrs.mangle
    # TODO: This depends on internals of the codegen
    # -> generates primitive name for flat spilling
    name = owner.name + "$enclosure"
    enclosure.name = name
    uid = 1
    while context.scope.lookup(enclosure.name):
        name = enclosure.name + f"_{uid}"
        enclosure.name = name
        uid += 1


def _consume_function_body_tokens(context: ParserContext) -> Generator[Token]:
    opened_context_blocks = 0

    context_keywords = (Keyword.IF, Keyword.DO, Keyword.LAMBDA_DEF)
    end_keyword_text = KEYWORD_TO_NAME[Keyword.END]

    while token := context.next_token():
        if token.type == TokenType.EOF:
            msg = f"Expected function to be closed but got end of file at {token.location}"
            raise ValueError(msg)
        if token.type != TokenType.KEYWORD:
            yield token
            continue

        if token.text == end_keyword_text:
            if opened_context_blocks <= 0:
                break
            opened_context_blocks -= 1

        is_context_keyword = WORD_TO_KEYWORD[token.text] in context_keywords
        if is_context_keyword:
            opened_context_blocks += 1

        yield token

    yield Token(
        type=TokenType.EOL,
        text="",
        value="",
        location=TokenLocation.toolchain(),
    )
