from __future__ import annotations

import sys
from typing import TYPE_CHECKING, NoReturn

from gofra.cli.output import cli_fatal_abort
from libgofra.lexer import tokenize_from_raw
from libgofra.lexer.io import open_source_file_line_stream
from libgofra.lexer.tokens import TokenLocation
from libgofra.preprocessor.macros.registry import registry_from_raw_definitions
from libgofra.preprocessor.preprocessor import preprocess_file

if TYPE_CHECKING:
    from gofra.cli.commands.build.arguments import BuildArguments


def cli_perform_preprocess_goal(args: BuildArguments) -> NoReturn:
    """Perform preprocess only goal that emits preprocessed tokens into stdout."""
    assert args.preprocess_only, (
        "Cannot perform preprocessor goal with no preprocessor flag set!"
    )

    if args.output_file_is_specified:
        return cli_fatal_abort(
            text="Output file has no effect for preprocess only goal, please pipe output via posix pipe (`>`) into desired file!",
        )

    macros_registry = registry_from_raw_definitions(
        location=TokenLocation.cli(),
        definitions=args.definitions,
    ).inject_propagated_defaults(target=args.target)

    path = args.source_filepath
    io = open_source_file_line_stream(path)
    lexer = tokenize_from_raw(path, io)
    preprocessor = preprocess_file(
        path,
        lexer,
        args.include_paths,
        macros=macros_registry,
    )

    for token in preprocessor:
        token_text = str(token.text)
        print(token_text, end=" ")

    return sys.exit(0)
