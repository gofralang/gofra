from __future__ import annotations

from collections import deque
from collections.abc import MutableSequence
from difflib import get_close_matches
from pathlib import Path
from typing import TYPE_CHECKING, MutableMapping, Sequence

from gofra.lexer import (
    Keyword,
    Token,
    TokenGenerator,
    TokenType,
    load_file_for_lexical_analysis,
)
from gofra.lexer.keywords import KEYWORD_TO_NAME, WORD_TO_KEYWORD
from gofra.parser.functions import Function
from gofra.parser.macros import Macro
from gofra.typecheck.types import WORD_TO_GOFRA_TYPE, GofraType

from ._context import ParserContext
from .exceptions import (
    ExternNoFunctionNameError,
    ParserEmptyIfBodyError,
    ParserEndAfterWhileError,
    ParserEndWithoutContextError,
    ParserExhaustiveContextStackError,
    ParserExternNonWordNameError,
    ParserExternRedefinesLanguageDefinitionError,
    ParserExternRedefinesMacroError,
    ParserIncludeFileNotFoundError,
    ParserIncludeNonStringNameError,
    ParserIncludeNoPathError,
    ParserIncludeSelfFileMacroError,
    ParserMacroNonWordNameError,
    ParserMacroRedefinesLanguageDefinitionError,
    ParserMacroRedefinitionError,
    ParserNoMacroNameError,
    ParserNoWhileBeforeDoError,
    ParserNoWhileConditionOperatorsError,
    ParserUnclosedMacroError,
    ParserUnfinishedIfBlockError,
    ParserUnfinishedWhileDoBlockError,
    ParserUnknownWordError,
)
from .intrinsics import WORD_TO_INTRINSIC
from .operators import OperatorType

if TYPE_CHECKING:
    from collections.abc import Iterable


def parse_file_into_operators(
    path: Path,
    include_search_directories: Iterable[Path],
) -> ParserContext:
    """Load file for parsing into operators (lex and then parse)."""
    tokens = load_file_for_lexical_analysis(source_filepath=path)
    return _parse_lexical_tokens_into_operators(
        path,
        tokens,
        include_search_directories=include_search_directories,
    )


def _parse_lexical_tokens_into_operators(
    parsing_from_path: Path,
    tokens: TokenGenerator | MutableSequence[Token],
    include_search_directories: Iterable[Path],
    *,
    context_propagated_macros: MutableMapping[str, Macro] | None = None,
    context_propagated_functions: MutableMapping[str, Function] | None = None,
) -> ParserContext:
    """Consumes token stream into language operators."""
    context = ParserContext(
        parsing_from_path=parsing_from_path,
        tokens=deque(reversed(list(tokens))),
        include_search_directories=include_search_directories,
        macros=context_propagated_macros or {},
        functions=context_propagated_functions or {},
    )

    while not context.tokens_exhausted():
        _consume_token_for_parsing(
            token=context.tokens.pop(),
            context=context,
        )

    if context.context_stack:
        _, unclosed_operator = context.pop_context_stack()
        match unclosed_operator.type:
            case OperatorType.DO | OperatorType.WHILE:
                raise ParserUnfinishedWhileDoBlockError(token=unclosed_operator.token)
            case OperatorType.IF:
                raise ParserUnfinishedIfBlockError(if_token=unclosed_operator.token)
            case _:
                raise ParserExhaustiveContextStackError

    return context


def _consume_token_for_parsing(token: Token, context: ParserContext) -> None:
    match token.type:
        case TokenType.INTEGER | TokenType.CHARACTER:
            return _push_integer_operator(context, token)
        case TokenType.STRING:
            return _push_string_operator(context, token)
        case TokenType.WORD:
            if _try_unpack_macro_or_inline_function_from_token(context, token):
                return None

            if _try_push_intrinsic_operator(context, token):
                return None

            raise ParserUnknownWordError(
                word_token=token,
                macro_names=context.macros.keys(),
                best_match=_best_match_for_word(context, token.text),
            )
        case TokenType.KEYWORD:
            return _consume_keyword_token(context, token)


def _best_match_for_word(context: ParserContext, word: str) -> str | None:
    matches = get_close_matches(word, WORD_TO_INTRINSIC.keys() | context.macros.keys())
    return matches[0] if matches else None


def _consume_keyword_token(context: ParserContext, token: Token) -> None:
    assert isinstance(token.value, Keyword)
    match token.value:
        case Keyword.IF | Keyword.DO | Keyword.WHILE | Keyword.END:
            return _consume_conditional_keyword_from_token(context, token)
        case Keyword.MACRO:
            return _consume_macro_definition_into_token(context, token)
        case Keyword.INCLUDE:
            return _unpack_include_from_token(context, token)
        case Keyword.INLINE | Keyword.EXTERN | Keyword.FUNCTION:
            return _unpack_function_definition_from_token(context, token)
        case Keyword.CALL:
            return _unpack_function_call_from_token(context, token)


def _consume_macro_definition_into_token(context: ParserContext, token: Token) -> None:
    if context.tokens_exhausted():
        raise ParserNoMacroNameError(macro_token=token)

    macro_name_token = context.tokens.pop()
    macro_name = macro_name_token.text

    if macro_name_token.type != TokenType.WORD:
        raise ParserMacroNonWordNameError(macro_name_token=macro_name_token)

    if macro_name in context.macros:
        raise ParserMacroRedefinitionError(
            redefine_macro_name_token=macro_name_token,
            original_macro_location=context.macros[macro_name].location,
        )

    if macro_name in (WORD_TO_INTRINSIC.keys() | WORD_TO_KEYWORD.keys()):
        raise ParserMacroRedefinesLanguageDefinitionError(
            macro_token=macro_name_token,
            macro_name=macro_name,
        )

    macro = context.new_macro(from_token=token, name=macro_name)

    opened_context_blocks = 0
    macro_was_closed = False

    context_keywords = (Keyword.IF, Keyword.MACRO, Keyword.DO)
    end_keyword_text = KEYWORD_TO_NAME[Keyword.END]

    original_token = token
    while not context.tokens_exhausted():
        token = context.tokens.pop()

        if token.type != TokenType.KEYWORD:
            macro.push_token(token)
            continue

        if token.text == end_keyword_text:
            if opened_context_blocks <= 0:
                macro_was_closed = True
                break
            opened_context_blocks -= 1

        is_context_keyword = WORD_TO_KEYWORD[token.text] in context_keywords
        if is_context_keyword:
            opened_context_blocks += 1

        macro.push_token(token)

    if not macro_was_closed:
        raise ParserUnclosedMacroError(
            macro_token=original_token,
            macro_name=macro_name,
        )


def _unpack_function_call_from_token(context: ParserContext, token: Token) -> None:
    if context.tokens_exhausted():
        raise NotImplementedError

    extern_call_name_token = context.tokens.pop()
    extern_call_name = extern_call_name_token.text

    if extern_call_name_token.type != TokenType.WORD:
        raise NotImplementedError

    target_function = context.functions.get(extern_call_name)
    if not target_function:
        raise NotImplementedError

    if target_function.is_inline:
        _try_unpack_macro_or_inline_function_from_token(context, extern_call_name_token)
        return

    context.push_new_operator(
        OperatorType.CALL,
        token,
        extern_call_name,
        is_contextual=False,
    )


def _unpack_function_modifiers(
    context: ParserContext,
    token: Token,
) -> tuple[Token, bool, bool]:
    """Return: [is_inline, is_extern]. Consumes tokens for modifiers."""
    modifier_is_inline = False
    modifier_is_extern = False

    while not context.tokens_exhausted():
        if token.type == TokenType.KEYWORD and token.value == Keyword.INLINE:
            if modifier_is_inline or modifier_is_extern:
                raise ValueError
            modifier_is_inline = True
            token = context.tokens.pop()

        if token.type == TokenType.KEYWORD and token.value == Keyword.EXTERN:
            if modifier_is_extern or modifier_is_inline:
                raise ValueError
            modifier_is_extern = True
            token = context.tokens.pop()

        if token.type == TokenType.KEYWORD and token.value == Keyword.FUNCTION:
            break

        raise ValueError

    assert not (modifier_is_extern and modifier_is_inline)
    return token, modifier_is_inline, modifier_is_extern


def _consume_function_definition_name_with_types(
    context: ParserContext,
    token: Token,
) -> tuple[GofraType, str, list[GofraType]]:
    if context.tokens_exhausted():
        raise ValueError

    return_type_token = context.tokens.pop()

    return_type = return_type_token.text
    if return_type not in WORD_TO_GOFRA_TYPE:
        raise ValueError
    return_type = WORD_TO_GOFRA_TYPE[return_type]

    if context.tokens_exhausted():
        raise ExternNoFunctionNameError(macro_token=token)

    function_sig_def_token = context.tokens.pop()
    function_sig_def = function_sig_def_token.text

    if "[" not in function_sig_def or "]" not in function_sig_def:
        raise ValueError

    function_name = function_sig_def.split("[")[0].strip()

    signature_types = function_sig_def.split("[")[1].split("]")[0].strip().split(",")
    signature_types = [WORD_TO_GOFRA_TYPE[t] for t in signature_types if t != ""]

    if function_sig_def_token.type != TokenType.WORD:
        raise ParserExternNonWordNameError(
            function_name_token=function_sig_def_token,
        )

    if function_name in context.macros:
        macro_reference = context.macros[function_name]
        raise ParserExternRedefinesMacroError(
            redefine_extern_function_name_token=function_sig_def_token,
            original_macro_name=macro_reference.name,
            original_macro_location=macro_reference.location,
        )

    if function_name in (WORD_TO_INTRINSIC.keys() | WORD_TO_KEYWORD.keys()):
        raise ParserExternRedefinesLanguageDefinitionError(
            extern_token=function_sig_def_token,
            extern_function_name=function_name,
        )

    return return_type, function_name, signature_types


def _unpack_function_definition_from_token(
    context: ParserContext,
    token: Token,
) -> None:
    token, modifier_is_inline, modifier_is_extern = _unpack_function_modifiers(
        context,
        token,
    )
    assert token.type == TokenType.KEYWORD
    assert token.value == Keyword.FUNCTION

    return_type, function_name, call_signature = (
        _consume_function_definition_name_with_types(context, token)
    )

    function = context.new_function(
        from_token=token,
        name=function_name,
        call_signature=call_signature,
        return_type=return_type,
        is_inline=modifier_is_inline,
        is_extern=modifier_is_extern,
    )

    if modifier_is_extern:
        return

    opened_context_blocks = 0
    function_was_closed = False

    context_keywords = (Keyword.IF, Keyword.DO)
    end_keyword_text = KEYWORD_TO_NAME[Keyword.END]

    original_token = token
    while not context.tokens_exhausted():
        token = context.tokens.pop()

        if token.type != TokenType.KEYWORD:
            function.push_token(token)
            continue

        if token.text == end_keyword_text:
            if opened_context_blocks <= 0:
                function_was_closed = True
                break
            opened_context_blocks -= 1

        is_context_keyword = WORD_TO_KEYWORD[token.text] in context_keywords
        if is_context_keyword:
            opened_context_blocks += 1

        function.push_token(token)

    if not function_was_closed:
        raise ParserUnclosedMacroError(
            macro_token=original_token,
            macro_name=function_name,
        )

    function.inner_body = _parse_lexical_tokens_into_operators(
        context.parsing_from_path,
        tokens=function.inner_tokens,
        include_search_directories=context.include_search_directories,
        context_propagated_functions=context.functions,
        context_propagated_macros=context.macros,
    ).operators


def _unpack_include_from_token(context: ParserContext, token: Token) -> None:
    if context.tokens_exhausted():
        raise ParserIncludeNoPathError(include_token=token)

    include_path_token = context.tokens.pop()
    include_path_raw = include_path_token.value

    if include_path_token.type != TokenType.STRING:
        raise ParserIncludeNonStringNameError(include_path_token=include_path_token)

    assert isinstance(include_path_raw, str)
    requested_include_path = Path(include_path_raw)

    if requested_include_path.absolute() == context.parsing_from_path.absolute():
        raise ParserIncludeSelfFileMacroError

    include_path = _resolve_real_import_path(requested_include_path, context)

    if include_path is None:
        raise ParserIncludeFileNotFoundError(
            include_token=token,
            include_path=requested_include_path,
        )

    already_included_sources = (n.resolve() for n in context.included_source_paths)
    if include_path.resolve() in already_included_sources:
        return

    context.included_source_paths.add(include_path)
    context.tokens.extend(reversed(list(load_file_for_lexical_analysis(include_path))))


def _resolve_real_import_path(
    requested_include_path: Path,
    context: ParserContext,
) -> Path | None:
    if requested_include_path.exists():
        return requested_include_path

    for include_search_directory in context.include_search_directories:
        load_from_path = include_search_directory.joinpath(requested_include_path)
        if load_from_path.exists():
            return load_from_path

    return None


def _consume_conditional_keyword_from_token(
    context: ParserContext,
    token: Token,
) -> None:
    assert isinstance(token.value, Keyword)
    match token.value:
        case Keyword.IF:
            return context.push_new_operator(
                type=OperatorType.IF,
                token=token,
                operand=None,
                is_contextual=True,
            )
        case Keyword.DO:
            if not context.has_context_stack():
                raise ParserNoWhileBeforeDoError(do_token=token)

            operator_while_idx, context_while = context.pop_context_stack()
            if context_while.type != OperatorType.WHILE:
                raise ParserNoWhileBeforeDoError(do_token=token)

            while_condition_len = context.current_operator - operator_while_idx - 1
            if while_condition_len == 0:
                raise ParserNoWhileConditionOperatorsError(
                    while_token=context_while.token,
                )

            operator = context.push_new_operator(
                type=OperatorType.DO,
                token=token,
                operand=None,
                is_contextual=True,
            )
            context.operators[-1].jumps_to_operator_idx = operator_while_idx
            return operator
        case Keyword.WHILE:
            return context.push_new_operator(
                type=OperatorType.WHILE,
                token=token,
                operand=None,
                is_contextual=True,
            )
        case Keyword.END:
            if not context.has_context_stack():
                raise ParserEndWithoutContextError(end_token=token)

            context_operator_idx, context_operator = context.pop_context_stack()

            context.push_new_operator(
                type=OperatorType.END,
                token=token,
                operand=None,
                is_contextual=False,
            )
            prev_context_jumps_at = context_operator.jumps_to_operator_idx
            context_operator.jumps_to_operator_idx = context.current_operator - 1

            match context_operator.type:
                case OperatorType.DO:
                    context.operators[-1].jumps_to_operator_idx = prev_context_jumps_at
                case OperatorType.IF:
                    if_body_size = context.current_operator - context_operator_idx - 2
                    if if_body_size == 0:
                        raise ParserEmptyIfBodyError(if_token=context_operator.token)
                case OperatorType.WHILE:
                    raise ParserEndAfterWhileError(end_token=token)
                case _:
                    raise AssertionError

            return None
        case _:
            raise AssertionError


def _try_unpack_macro_or_inline_function_from_token(
    context: ParserContext,
    token: Token,
) -> bool:
    assert token.type == TokenType.WORD

    inline_block = context.macros.get(token.text, None) or context.functions.get(
        token.text,
        None,
    )
    if inline_block:
        if isinstance(inline_block, Function) and (
            not inline_block.is_inline or inline_block.is_extern
        ):
            raise NotImplementedError
        context.expand_from_inline_block(inline_block)

    return bool(inline_block)


def _push_string_operator(context: ParserContext, token: Token) -> None:
    assert isinstance(token.value, str)
    context.push_new_operator(
        type=OperatorType.PUSH_STRING,
        token=token,
        operand=token.value,
        is_contextual=False,
    )


def _push_integer_operator(context: ParserContext, token: Token) -> None:
    assert isinstance(token.value, int)
    context.push_new_operator(
        type=OperatorType.PUSH_INTEGER,
        token=token,
        operand=token.value,
        is_contextual=False,
    )


def _try_push_intrinsic_operator(context: ParserContext, token: Token) -> bool:
    assert isinstance(token.value, str)
    intrinsic = WORD_TO_INTRINSIC.get(token.value)

    if intrinsic is None:
        return False

    context.push_new_operator(
        type=OperatorType.INTRINSIC,
        token=token,
        operand=intrinsic,
        is_contextual=False,
    )
    return True
