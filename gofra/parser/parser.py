from collections import deque
from pathlib import Path

from gofra.lexer import (
    Keyword,
    Token,
    TokenGenerator,
    TokenType,
    load_file_for_lexical_analysis,
)
from gofra.lexer.exceptions import LexerFileNotFoundError
from gofra.lexer.keywords import KEYWORD_TO_NAME, WORD_TO_KEYWORD

from ._context import ParserContext
from .exceptions import (
    ParserEmptyIfBodyError,
    ParserEndAfterWhileError,
    ParserEndWithoutContextError,
    ParserExhaustiveContextStackError,
    ParserIncludeFileNotFoundError,
    ParserIncludeNonStringNameError,
    ParserIncludeNoPathError,
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


def parse_file_into_operators(path: Path) -> ParserContext:
    """Load file for parsing into operators (lex and then parse)."""
    tokens = load_file_for_lexical_analysis(source_filepath=path)
    return _parse_lexical_tokens_into_operators(tokens)


def _parse_lexical_tokens_into_operators(tokens: TokenGenerator) -> ParserContext:
    """Consumes token stream into language operators."""
    context = ParserContext(
        tokens=deque(reversed(list(tokens))),
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
            if _try_unpack_macro_from_token(context, token):
                return None

            if _try_push_intrinsic_operator(context, token):
                return None

            raise ParserUnknownWordError(
                word_token=token,
                macro_names=context.macros.keys(),
            )
        case TokenType.KEYWORD:
            return _consume_keyword_token(context, token)


def _consume_keyword_token(context: ParserContext, token: Token) -> None:
    assert isinstance(token.value, Keyword)
    match token.value:
        case Keyword.IF | Keyword.DO | Keyword.WHILE | Keyword.END:
            return _consume_conditional_keyword_from_token(context, token)
        case Keyword.MACRO:
            return _consume_macro_definition_into_token(context, token)

        case Keyword.INCLUDE:
            return _unpack_include_from_token(context, token)


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


def _unpack_include_from_token(context: ParserContext, token: Token) -> None:
    if context.tokens_exhausted():
        raise ParserIncludeNoPathError(include_token=token)

    include_path_token = context.tokens.pop()
    include_path_raw = include_path_token.value

    if include_path_token.type != TokenType.STRING:
        raise ParserIncludeNonStringNameError(include_path_token=include_path_token)

    assert isinstance(include_path_raw, str)
    include_path = Path(include_path_raw)

    try:
        include_tokens = list(load_file_for_lexical_analysis(include_path))
    except LexerFileNotFoundError as e:
        raise ParserIncludeFileNotFoundError(
            include_token=token,
            include_path=include_path,
        ) from e
    context.tokens.extend(deque(reversed(include_tokens)))


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


def _try_unpack_macro_from_token(context: ParserContext, token: Token) -> bool:
    assert token.type == TokenType.WORD
    macro = context.macros.get(token.text, None)
    if macro:
        context.expand_from_macro(macro)

    return macro is not None


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
