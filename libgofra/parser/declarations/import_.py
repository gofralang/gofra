from pathlib import Path

from libgofra.feature_flags import FEATURE_ALLOW_MODULES
from libgofra.lexer import Keyword, Token, TokenType
from libgofra.parser._context import ParserContext


def parse_import_declaration(context: ParserContext, token: Token) -> None:
    if not FEATURE_ALLOW_MODULES:
        msg = "Import feature is not enabled, required to import modules\nModules is still Work-In-Progress, expect possible errors and caveats while using them"
        raise ValueError(msg)
    requested_import_path = _consume_import_raw_path_from_token(context, token)

    # `as` expected
    peeked = context.peek_token()
    named_import_as_name = str(requested_import_path)
    if peeked.type == TokenType.KEYWORD and peeked.value == Keyword.AS:
        context.advance_token()  # consume `as`
        as_name_token = context.next_token()
        assert isinstance(as_name_token.value, str)
        assert as_name_token.type in (TokenType.IDENTIFIER, TokenType.STRING)
        named_import_as_name = as_name_token.value

    if requested_import_path.resolve(strict=False) == context.path:
        msg = f"Tried to import self at {context.path}"
        raise ValueError(msg)

    context.on_import_request(named_import_as_name, requested_import_path)


def _consume_import_raw_path_from_token(
    context: ParserContext,
    include_token: Token,
) -> Path:
    """Consume include path from `include` construction."""
    assert include_token.type == TokenType.KEYWORD
    assert include_token.value == Keyword.MODULE_IMPORT

    import_token = context.next_token()
    if not import_token:
        msg = "no import name"
        raise ValueError(msg)
    if import_token.type not in (TokenType.STRING, TokenType.IDENTIFIER):
        msg = f"import not a string or identifier at {import_token.location}"
        raise ValueError(msg)

    include_path_raw = import_token.value
    assert isinstance(include_path_raw, str)
    return Path(include_path_raw)
