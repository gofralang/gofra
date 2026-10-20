from __future__ import annotations

from difflib import get_close_matches
from typing import TYPE_CHECKING, assert_never

from libgofra.feature_flags import FEATURE_ALLOW_FPU
from libgofra.hir.function import Function
from libgofra.hir.operator import FunctionCallOperand
from libgofra.hir.variable import Variable
from libgofra.lexer import (
    Keyword,
    Token,
    TokenType,
)
from libgofra.lexer.keywords import PreprocessorKeyword
from libgofra.parser.declarations.import_ import parse_import_declaration
from libgofra.parser.declarations.type import parse_type_declaration
from libgofra.parser.definitions.structure import (
    parse_structure_definition,
)
from libgofra.parser.errors.keyword_in_without_loop_block import (
    KeywordInWithoutLoopBlockError,
)
from libgofra.parser.errors.local_level_keyword_in_global_scope import (
    LocalLevelKeywordInGlobalScopeError,
)
from libgofra.parser.errors.top_level_expected_no_operators import (
    TopLevelExpectedNoOperatorsError,
)
from libgofra.parser.errors.top_level_keyword_in_local_scope import (
    TopLevelKeywordInLocalScopeError,
)
from libgofra.parser.exprs.primitives import (
    push_float_operator,
    push_integer_operator,
    push_string_operator,
    try_push_intrinsic_operator,
)
from libgofra.parser.scope import Scope
from libgofra.types import BoolType
from libgofra.types.composite.function import FunctionType

from ._context import ParserContext, TokenStream
from .definitions.function import (
    parse_function_definition,
    parse_lambda_function_definition,
)
from .definitions.union import parse_union_definition
from .definitions.variable import parse_variable_definition
from .exceptions import (
    ParserDirtyNonPreprocessedTokenError,
    ParserExhaustiveContextStackError,
    ParserUnfinishedIfBlockError,
    ParserUnfinishedWhileDoBlockError,
    ParserUnknownIdentifierError,
)
from .intrinsics.align_of import parse_align_of_intrinsic
from .intrinsics.compile_time_error import parse_compile_time_error_rintrinsic
from .intrinsics.inline_assembly import parse_inline_assembly_intrinsic
from .intrinsics.offset_of import parse_offset_of_intrinsic
from .intrinsics.pointer_of_proc import parse_pointer_of_proc_intrinsic
from .intrinsics.size_of import parse_size_of_intrinsic
from .intrinsics.syscall import parse_syscall_intrinsic
from .intrinsics.typecast import parse_typecast_intrinsic
from .operators import IDENTIFIER_TO_OPERATOR_TYPE, OperatorType
from .statements.control_flow import (
    consume_conditional_block_keyword_from_token,
)
from .variable_accessor import try_parse_variable_accessor_expr

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path

    from libgofra.hir.module import Module


TOP_LEVEL_KEYWORD = (
    Keyword.ATTR_FUNC_INLINE,
    Keyword.ATTR_FUNC_EXTERN,
    Keyword.ATTR_FUNC_NO_RETURN,
    Keyword.ATTR_FUNC_PUBLIC,
    Keyword.ATTR_FUNC_NAKED,
    Keyword.ATTR_STRUCT_REORDER,
    Keyword.ATTR_STRUCT_PACKED,
    Keyword.FUNCTION,
    Keyword.STRUCT,
    Keyword.UNION,
    Keyword.TYPE_DEFINE,
    Keyword.MODULE_IMPORT,
)

BOTH_LEVEL_KEYWORD = (
    Keyword.CONST_DEFINE,
    Keyword.END,
    Keyword.VARIABLE_DEFINE,
    Keyword.COMPILE_TIME_ERROR,
)


def parse_module_from_tokenizer(
    module: Module,
    tokenizer: Generator[Token],
    *,
    rt_array_oob_check: bool = False,
    entry_point_name: str,
    on_import_request: Callable[[str, Path], None],
) -> Module:
    """Load file for parsing into operators."""
    context = ParserContext(
        module=module,
        scope=Scope(parent=None),
        tokens=TokenStream(tokenizer),
        rt_array_oob_check=rt_array_oob_check,
        entry_point_name=entry_point_name,
        on_import_request=on_import_request,
    )
    _parse_from_context_into_operators(context=context)

    assert context.scope.is_global, (
        "Parser context in result of parsing must an top level, bug in a parser"
    )
    if context.operators:
        raise TopLevelExpectedNoOperatorsError(context.operators[0])

    context.finalize()

    return module


def _parse_from_context_into_operators(context: ParserContext) -> None:
    """Consumes token stream into language operators."""
    try:
        while token := context.next_token():
            _consume_token_for_parsing(
                token=token,
                context=context,
            )
    except StopIteration:
        pass

    if context.context_stack:
        _, unclosed_operator, *_ = context.pop_context_stack()
        match unclosed_operator.type:
            case OperatorType.CONDITIONAL_DO | OperatorType.CONDITIONAL_WHILE:
                raise ParserUnfinishedWhileDoBlockError(token=unclosed_operator.token)
            case OperatorType.CONDITIONAL_IF:
                raise ParserUnfinishedIfBlockError(if_token=unclosed_operator.token)
            case _:
                raise ParserExhaustiveContextStackError


def _consume_token_for_parsing(token: Token, context: ParserContext) -> None:  # noqa: PLR0911
    match token.type:
        case TokenType.INTEGER | TokenType.CHARACTER:
            return push_integer_operator(context, token)
        case TokenType.FLOAT:
            if not FEATURE_ALLOW_FPU:
                msg = "FPU is disabled as feature for being in unstable test stage, try enable `FEATURE_ALLOW_FPU` to access FP."
                raise ValueError(msg)
            return push_float_operator(context, token)
        case TokenType.STRING:
            return push_string_operator(context, token)
        case TokenType.IDENTIFIER:
            return _consume_word_token(token, context)
        case TokenType.KEYWORD:
            return _consume_keyword_token(context, token)
        case TokenType.EOL | TokenType.EOF:
            return None
        case TokenType.STAR:
            assert not context.scope.is_global
            context.push_new_operator(OperatorType.ARITHMETIC_MULTIPLY, token=token)
            return None
        case TokenType.SEMICOLON:
            # Treat semicolon as simple line break should be fine except this may be caught in some complex constructions checks
            return None
        case (
            TokenType.LBRACKET
            | TokenType.RBRACKET
            | TokenType.LPAREN
            | TokenType.RPAREN
            | TokenType.DOT
            | TokenType.COMMA
            | TokenType.COLON
            | TokenType.RCURLY
            | TokenType.LCURLY
            | TokenType.ASSIGNMENT
        ):
            msg = f"Got {token.type.name} ({token.location}) in form of an single parser-expression (non-composite). This token (as other symbol-defined ones) must occur only in composite expressions (e.g function signature, type constructions)."
            raise ValueError(msg)
        case _:
            assert_never(token.type)


def _consume_word_token(token: Token, context: ParserContext) -> None:
    if try_push_intrinsic_operator(context, token):
        return

    if _try_unpack_function_call_from_identifier_token(context, token):
        return

    if try_parse_variable_accessor_expr(context, token):
        return

    raise ParserUnknownIdentifierError(
        word_token=token,
        best_match=_best_match_for_word(context, token.text),
    )


def _best_match_for_word(context: ParserContext, word: str) -> str | None:
    matches = get_close_matches(
        word,
        IDENTIFIER_TO_OPERATOR_TYPE.keys()
        | context.scope.functions.keys()
        | context.scope.variables.keys(),
    )
    return matches[0] if matches else None


def _consume_keyword_token(context: ParserContext, token: Token) -> None:  # noqa: PLR0911
    if isinstance(token.value, PreprocessorKeyword):
        raise ParserDirtyNonPreprocessedTokenError(token=token)
    assert isinstance(token.value, Keyword)

    if context.scope.is_global:
        if token.value not in (*TOP_LEVEL_KEYWORD, *BOTH_LEVEL_KEYWORD):
            raise LocalLevelKeywordInGlobalScopeError(token)
    elif token.value in TOP_LEVEL_KEYWORD:
        raise TopLevelKeywordInLocalScopeError(token)

    match token.value:
        case Keyword.VARIABLE_DEFINE | Keyword.CONST_DEFINE:
            return parse_variable_definition(context, token)
        case Keyword.STRUCT:
            return parse_structure_definition(context)
        case Keyword.UNION:
            return parse_union_definition(context)
        case Keyword.COMPILE_TIME_ERROR:
            return parse_compile_time_error_rintrinsic(context, token)
        case Keyword.SYSCALL:
            return parse_syscall_intrinsic(context, token)
        case Keyword.ALIGN_OF:
            return parse_align_of_intrinsic(context, token)
        case Keyword.SIZEOF:
            return parse_size_of_intrinsic(context, token)
        case Keyword.MODULE_IMPORT:
            return parse_import_declaration(context, token)
        case Keyword.OFFSET_OF:
            return parse_offset_of_intrinsic(context, token)
        case Keyword.POINTER_OF_PROC:
            return parse_pointer_of_proc_intrinsic(context, token)
        case (
            Keyword.IF
            | Keyword.DO
            | Keyword.WHILE
            | Keyword.END
            | Keyword.FOR
            | Keyword.ELSE
        ):
            return consume_conditional_block_keyword_from_token(context, token)
        case (
            Keyword.FUNCTION
            | Keyword.ATTR_FUNC_INLINE
            | Keyword.ATTR_FUNC_EXTERN
            | Keyword.ATTR_FUNC_PUBLIC
            | Keyword.ATTR_FUNC_NO_RETURN
            | Keyword.ATTR_FUNC_NAKED
            | Keyword.ATTR_FUNC_NO_MANGLE
        ):
            return parse_function_definition(context, token)
        case Keyword.FUNCTION_CALL:
            return _unpack_function_call_from_token(context, token)
        case Keyword.FUNCTION_RETURN:
            return context.push_new_operator(OperatorType.FUNCTION_RETURN, token=token)
        case Keyword.TYPE_CAST:
            return parse_typecast_intrinsic(context, token)

        case Keyword.DEBUGGER_BREAKPOINT | Keyword.COPY | Keyword.DROP | Keyword.SWAP:
            return context.push_new_operator(
                type={
                    Keyword.DEBUGGER_BREAKPOINT: OperatorType.DEBUGGER_BREAKPOINT,
                    Keyword.COPY: OperatorType.STACK_COPY,
                    Keyword.DROP: OperatorType.STACK_DROP,
                    Keyword.SWAP: OperatorType.STACK_SWAP,
                }[token.value],
                token=token,
            )

        case Keyword.TRUE | Keyword.FALSE:
            # TODO: literal
            context.push_new_operator(
                OperatorType.PUSH_INTEGER,
                token=token,
                operand=int(token.value == Keyword.TRUE),
            )
            return context.push_new_operator(
                OperatorType.STATIC_TYPE_CAST,
                token,
                BoolType(),
                is_contextual=False,
            )
        case Keyword.IN:
            raise KeywordInWithoutLoopBlockError(token)
        case Keyword.INLINE_RAW_ASM:
            return parse_inline_assembly_intrinsic(context, token)

        case Keyword.LAMBDA_DEF:
            return parse_lambda_function_definition(context, token)
        case Keyword.TYPE_DEFINE:
            return parse_type_declaration(context)
        case Keyword.AS:
            msg = f"As keyword may used only in import statements for now at {token.location}"
            raise ValueError(msg)
        case Keyword.ATTR_STRUCT_PACKED | Keyword.ATTR_STRUCT_REORDER:
            raise ValueError
        case _:
            assert_never(token.value)


def _unpack_function_call_from_token(context: ParserContext, token: Token) -> None:
    name_token = context.next_token()
    if name_token.type != TokenType.IDENTIFIER:
        msg = "expected function name as identifier after `call`"
        raise ValueError(msg)

    owner_module: str | None = None
    if context.peek_token().type == TokenType.DOT:
        # Module level call
        context.advance_token()
        context.expect_token(TokenType.IDENTIFIER)
        module_tok = context.next_token()
        module_tok, name_token = name_token, module_tok
        assert isinstance(module_tok.value, str)
        owner_module = module_tok.value

    name = name_token.text
    function = context.scope.lookup(name)
    call_spec = FunctionCallOperand(module=owner_module, func=name)

    if isinstance(function, Variable):
        variable = context.scope.variables[name]
        assert isinstance(variable.type, FunctionType)
        context.push_new_operator(
            OperatorType.PUSH_VARIABLE_VALUE,
            token=token,
            operand=name,
        )
        context.push_new_operator(
            OperatorType.FUNCTION_CALL_FROM_STACK_POINTER,
            token=token,
            operand=variable.type,
        )
        return
    assert function is None or isinstance(function, Function), function

    if function and function.attrs.inline:
        assert not function.attrs.external
        context.expand_from_inline_block(function)
        return

    context.push_new_operator(
        OperatorType.FUNCTION_CALL,
        token=token,
        operand=call_spec,
    )


def _try_unpack_function_call_from_identifier_token(
    context: ParserContext,
    token: Token,
) -> bool:
    assert token.type == TokenType.IDENTIFIER

    name = token.text
    function = context.scope.lookup(name)
    if function and isinstance(function, Function):
        if function.attrs.inline:
            context.expand_from_inline_block(function)
            return True
        call_spec = FunctionCallOperand(module=None, func=function)
        context.push_new_operator(
            type=OperatorType.FUNCTION_CALL,
            token=token,
            operand=call_spec,
        )
        return True
    return False
