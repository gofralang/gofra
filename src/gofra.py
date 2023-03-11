"""
    Main Gofra programming language source code.

"""

__author__ = "Kirill Zhosul @kirillzhosul"
__license__ = "MIT"

from typing import Generator
from sys import argv
from os.path import basename

import gofra
from gofra.core.stack import Stack
from gofra.core.danger import *
from gofra.core import vm

# MAJOR WARNING FOR ALL READERS.
# This code is not refactored,
# currently I am working on refactoring and splitting into the gofra module,
# there is a lot of stuff, that will be reworked.

# Also, want to say that bytecode is not finished, and interpretation will be
# converted to gofra.core.vm that will be run bytecode for own,
# as internal interpretation method (if you want to use C++ VM which is may not be finished also yet,
# see that https://github.com/gofralang/vm/)


# Lexer.


def lexer_tokenize(lines: List[str], file_parent: str) -> Generator[Token, None, None]:
    """Tokenizes lines into list of the Tokens."""

    # Check that there is no changes in token type.
    assert (
        len(TokenType) == 6
    ), "Please update implementation after adding new TokenType!"

    # Get the basename.
    file_parent = basename(file_parent)

    # Current line index.
    current_line_index = 0

    # Get lines count.
    lines_count = len(lines)

    # Check that there is more than zero lines.
    if lines_count == 0:
        # If there is no lines.

        # Error.
        gofra.core.errors.message_verbosed(
            Stage.LEXER,
            (file_parent, 1, 1),
            "Error",
            "There is no lines found in the given file " "are you given empty file?",
            True,
        )

    while current_line_index < lines_count:
        # Loop over lines.

        # Get line.
        current_line = lines[current_line_index]

        # Find first non-space char.
        current_collumn_index = gofra.core.lexer.find_collumn(
            current_line, 0, lambda char: not char.isspace()
        )

        # Get current line length.
        current_line_length = len(current_line)

        # ?.
        current_collumn_end_index = 0

        while current_collumn_index < current_line_length:
            # Iterate over line.

            # Get the location.
            current_location = (
                file_parent,
                current_line_index + 1,
                current_collumn_index + 1,
            )

            if current_line[current_collumn_index] == EXTRA_CHAR:
                # If we got character quote*.
                # Index of the column end.
                # (Trying to find closing quote*
                current_collumn_end_index = gofra.core.lexer.find_collumn(
                    current_line,
                    current_collumn_index + 1,
                    lambda char: char == EXTRA_CHAR,
                )

                if (
                    current_collumn_end_index >= len(current_line)
                    or current_line[current_collumn_end_index] != EXTRA_CHAR
                ):
                    # If we got not EXTRA_CHAR or exceed current line length.

                    # Error.
                    gofra.core.errors.message_verbosed(
                        Stage.LEXER,
                        current_location,
                        "Error",
                        "There is unclosed character literal. "
                        f"Do you forgot to place `{EXTRA_CHAR}`?",
                        True,
                    )

                # Get current token text.
                current_token_text = current_line[
                    current_collumn_index + 1 : current_collumn_end_index
                ]

                # Get current char value.
                current_char_value = gofra.core.lexer.unescape(
                    current_token_text
                ).encode("UTF-8")

                if len(current_char_value) != 1:
                    # If there is 0 or more than 1 characters*.

                    # Error.
                    gofra.core.errors.message_verbosed(
                        Stage.LEXER,
                        current_location,
                        "Error",
                        "Unexpected number of characters in the character literal."
                        "Only one character is allowed in character literal",
                        True,
                    )
                # Return character token.
                yield Token(
                    type=TokenType.CHARACTER,
                    text=current_token_text,
                    location=current_location,
                    value=current_char_value[0],
                )

                # Find first non-space char.
                current_collumn_index = gofra.core.lexer.find_collumn(
                    current_line,
                    current_collumn_end_index + 1,
                    lambda char: not char.isspace(),
                )
            elif current_line[current_collumn_index] == EXTRA_STRING:
                # If this is string.

                # String buffer for strings.
                current_string_buffer = ""

                while current_line_index < len(lines):
                    # While we don`t reach end of the lines.

                    # Get string start.
                    string_start_collumn_index = current_collumn_index

                    if current_string_buffer == "":
                        # If we not start writing string buffer.

                        # Increment by one for quote.
                        string_start_collumn_index += len(EXTRA_STRING)
                    else:
                        # If we started.

                        # Just grab line.
                        current_line = lines[current_line_index]

                    # Get string end.
                    string_end_collumn_index = gofra.core.lexer.find_string_end(
                        current_line, string_start_collumn_index
                    )

                    if (
                        string_end_collumn_index >= len(current_line)
                        or current_line[string_end_collumn_index] != EXTRA_STRING
                    ):
                        # If got end of current line, or not found closing string.

                        # Add current line.
                        current_string_buffer += current_line[
                            string_start_collumn_index:
                        ]

                        # Reset and move next line.
                        current_line_index += 1
                        current_collumn_index = 0
                    else:
                        # If current line.

                        # Add final buffer.
                        current_string_buffer += current_line[
                            string_start_collumn_index:string_end_collumn_index
                        ]
                        current_collumn_end_index = string_end_collumn_index

                        # End lexing string.
                        break

                if current_line_index >= len(lines):
                    # If we exceed current lines length.

                    # Error.
                    gofra.core.errors.message_verbosed(
                        Stage.LEXER,
                        current_location,
                        "Error",
                        "There is unclosed string literal. "
                        f"Do you forgot to place `{EXTRA_STRING}`?",
                        True,
                    )
                # Error?.
                assert (
                    current_line[current_collumn_index] == EXTRA_STRING
                ), "Got non string closing character!"

                # Increase end index.
                current_collumn_end_index += 1

                # Get current token text.
                current_token_text = current_string_buffer

                # Return string token.
                yield Token(
                    type=TokenType.STRING,
                    text=current_token_text,
                    location=current_location,
                    value=gofra.core.lexer.unescape(current_token_text),
                )

                # Find first non-space char.
                current_collumn_index = gofra.core.lexer.find_collumn(
                    current_line,
                    current_collumn_end_index,
                    lambda char: not char.isspace(),
                )
            else:
                # Index of the column end.
                current_collumn_end_index = gofra.core.lexer.find_collumn(
                    current_line, current_collumn_index, lambda char: char.isspace()
                )

                # Get current token text.
                current_token_text = current_line[
                    current_collumn_index:current_collumn_end_index
                ]

                try:
                    # Try convert token integer.
                    current_token_integer = int(current_token_text)
                except ValueError:
                    # If there is invalid value for integer.

                    if current_token_text in KEYWORD_NAMES_TO_TYPE:
                        # If this is keyword.

                        # Return keyword token.
                        yield Token(
                            type=TokenType.KEYWORD,
                            text=current_token_text,
                            location=current_location,
                            value=KEYWORD_NAMES_TO_TYPE[current_token_text],
                        )
                    else:
                        # Not keyword.

                        # If this is comment - break.
                        # TODO: Try to fix something like 0//0 (comment not at the start) will lex not as should.
                        if current_token_text.startswith(EXTRA_COMMENT):
                            break

                        # Return word token.
                        yield Token(
                            type=TokenType.WORD,
                            text=current_token_text,
                            location=current_location,
                            value=current_token_text,
                        )
                else:
                    # If all ok.

                    # Return token.
                    yield Token(
                        type=TokenType.INTEGER,
                        text=current_token_text,
                        location=current_location,
                        value=current_token_integer,
                    )

                # Find first non-space char.
                current_collumn_index = gofra.core.lexer.find_collumn(
                    current_line,
                    current_collumn_end_index,
                    lambda char: not char.isspace(),
                )

        # Increment current line.
        current_line_index += 1


# Parser.


def parser_parse(tokens: List[Token], context: ParserContext, path: str):
    """Parses token from lexer* (lexer_tokenize())"""

    # Check that there is no changes in operator type.
    assert (
        len(OperatorType) == 10
    ), "Please update implementation after adding new OperatorType!"

    # Check that there is no changes in keyword type.
    assert len(Keyword) == 6, "Please update implementation after adding new Keyword!"

    # Check that there is no changes in token type.
    assert (
        len(TokenType) == 6
    ), "Please update implementation after adding new TokenType!"

    # Reverse tokens.
    reversed_tokens: List[Token] = list(reversed(tokens))

    # Definitions.
    definitions: Dict[str, Definition] = dict()

    if len(reversed_tokens) == 0:
        gofra.core.errors.message_verbosed(
            Stage.PARSER,
            (basename(path), 1, 1),
            "Error",
            "There is no tokens found, are you given empty file?",
            True,
        )

    while len(reversed_tokens) > 0:
        # While there is any token.

        # Get current token.
        current_token: Token = reversed_tokens.pop()

        if current_token.type == TokenType.WORD:
            assert isinstance(
                current_token.value, str
            ), "Type error, lexer level error?"

            if current_token.value in INTRINSIC_NAMES_TO_TYPE:
                context.operators.append(
                    Operator(
                        type=OperatorType.INTRINSIC,
                        token=current_token,
                        operand=INTRINSIC_NAMES_TO_TYPE[current_token.value],
                    )
                )
                context.operator_index += 1
                continue

            if current_token.text in definitions:
                # Expand definition tokens.
                reversed_tokens += reversed(definitions[current_token.text].tokens)
                continue

            if current_token.text.startswith(EXTRA_DIRECTIVE):
                directive = current_token.text[len(EXTRA_DIRECTIVE) :]
                if directive.startswith("MEM_BUF_BYTE_SIZE="):
                    # If this is starts with memory buffer byte size definition name.

                    # Get directive value from all directive text.
                    directive_value = directive[len("MEM_BUF_BYTE_SIZE=") :]

                    # Get new memory size
                    try:
                        new_memory_bytearray_size = int(directive_value)
                    except ValueError:
                        gofra.core.errors.message_verbosed(
                            Stage.PARSER,
                            current_token.location,
                            "Error",
                            f"Directive `{EXTRA_DIRECTIVE}{directive}` "
                            f"passed invalid size `{directive_value}`!",
                            True,
                        )
                    else:
                        # Change size of the bytearray.
                        context.memory_bytearray_size = new_memory_bytearray_size
                else:
                    # Message.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        current_token.location,
                        "Error",
                        f"Unknown directive `{EXTRA_DIRECTIVE}{directive}`",
                        True,
                    )
                continue

            gofra.core.errors.message_verbosed(
                Stage.PARSER,
                current_token.location,
                "Error",
                f"Unknown WORD `{current_token.text}`, "
                f"are you misspelled something?",
                True,
            )
        elif current_token.type == TokenType.INTEGER:
            # If we got an integer.

            # Type check.
            assert isinstance(
                current_token.value, int
            ), "Type error, lexer level error?"

            # Add operator to the context.
            context.operators.append(
                Operator(
                    type=OperatorType.PUSH_INTEGER,
                    token=current_token,
                    operand=current_token.value,
                )
            )

            # Increment operator index.
            context.operator_index += 1
        elif current_token.type == TokenType.STRING:
            # If we got a string.

            # Type check.
            assert isinstance(
                current_token.value, str
            ), "Type error, lexer level error?"

            # Add operator to the context.
            context.operators.append(
                Operator(
                    type=OperatorType.PUSH_STRING,
                    token=current_token,
                    operand=current_token.value,
                )
            )

            # Increment operator index.
            context.operator_index += 1
        elif current_token.type == TokenType.CHARACTER:
            # If we got a character.

            # Type check.
            assert isinstance(
                current_token.value, int
            ), "Type error, lexer level error?"

            # Add operator to the context.
            context.operators.append(
                Operator(
                    type=OperatorType.PUSH_INTEGER,
                    token=current_token,
                    operand=current_token.value,
                )
            )

            # Increment operator index.
            context.operator_index += 1
        elif current_token.type == TokenType.KEYWORD:
            # If we got a keyword.

            if current_token.value == Keyword.IF:
                # This is IF keyword.

                # Push operator to the context.
                context.operators.append(
                    Operator(type=OperatorType.IF, token=current_token)
                )

                # Push current operator index to the context memory stack.
                context.memory_stack.append(context.operator_index)

                # Increment operator index.
                context.operator_index += 1
            elif current_token.value == Keyword.WHILE:
                # This is WHILE keyword.

                # Push operator to the context.
                context.operators.append(
                    Operator(type=OperatorType.WHILE, token=current_token)
                )

                # Push current operator index to the context memory stack.
                context.memory_stack.append(context.operator_index)

                # Increment operator index.
                context.operator_index += 1
            elif current_token.value == Keyword.DO:
                # This is `DO` keyword.

                if len(context.memory_stack) == 0:
                    # If there is nothing on the memory stack.

                    # Error.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        current_token.location,
                        "Error",
                        "`do` should used after the `while` block!",
                        True,
                    )

                # Push operator to the context.
                context.operators.append(
                    Operator(type=OperatorType.DO, token=current_token)
                )

                # Get `WHILE` operator from the memory stack.
                block_operator_index = context.memory_stack.pop()
                block_operator = context.operators[block_operator_index]

                if block_operator.type != OperatorType.WHILE:
                    # If this is not while.

                    # Error.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        current_token.location,
                        "Error",
                        "`do` should used after the `while` block!",
                        True,
                    )

                # Say that we crossreference WHILE block.
                context.operators[context.operator_index].operand = block_operator_index

                # Push current operator index to the context memory stack.
                context.memory_stack.append(context.operator_index)

                # Increment operator index.
                context.operator_index += 1
            elif current_token.value == Keyword.ELSE:
                # If this is else keyword.

                if len(context.memory_stack) == 0:
                    # If there is nothing on the memory stack.

                    # Error.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        current_token.location,
                        "Error",
                        "`else` should used after the `if` block!",
                        True,
                    )

                # Get `IF` operator from the memory stack.
                block_operator_index = context.memory_stack.pop()
                block_operator = context.operators[block_operator_index]

                if block_operator.type == OperatorType.IF:
                    # If we use else after the IF.

                    # Say that previous IF should jump at the our+1 operator index.
                    context.operators[block_operator_index].operand = (
                        context.operator_index + 1
                    )

                    # Push current operator index to the stack.
                    context.memory_stack.append(context.operator_index)

                    # Push operator to the context.
                    context.operators.append(
                        Operator(type=OperatorType.ELSE, token=current_token)
                    )

                    # Increment operator index.
                    context.operator_index += 1
                else:
                    # If not `IF`.

                    # Get error location.
                    error_location = block_operator.token.location

                    # Error message.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        error_location,
                        "Error",
                        "`else` can only used after `if` block!",
                        True,
                    )
            elif current_token.value == Keyword.END:
                # If this is end keyword.

                # Get block operator from the stack.
                block_operator_index = context.memory_stack.pop()
                block_operator = context.operators[block_operator_index]

                if block_operator.type == OperatorType.IF:
                    # If this is IF block.

                    # Push operator to the context.
                    context.operators.append(
                        Operator(type=OperatorType.END, token=current_token)
                    )

                    # Say that start IF block refers to this END block.
                    context.operators[
                        block_operator_index
                    ].operand = context.operator_index

                    # Say that this END block refers to next operator index.
                    context.operators[context.operator_index].operand = (
                        context.operator_index + 1
                    )
                elif block_operator.type == OperatorType.ELSE:
                    # If this is ELSE block.

                    # Push operator to the context.
                    context.operators.append(
                        Operator(type=OperatorType.END, token=current_token)
                    )

                    # Say that owner block (If/Else) should jump to us.
                    context.operators[
                        block_operator_index
                    ].operand = context.operator_index

                    # Say that we should jump to the next position.
                    context.operators[context.operator_index].operand = (
                        context.operator_index + 1
                    )
                elif block_operator.type == OperatorType.DO:
                    # If this is DO block.

                    # Type check.
                    assert (
                        block_operator.operand is not None
                    ), "DO operator has unset operand! Parser level error?"
                    assert isinstance(
                        block_operator.operand, OPERATOR_ADDRESS
                    ), "Type error, parser level error?"

                    # Push operator to the context.
                    context.operators.append(
                        Operator(type=OperatorType.END, token=current_token)
                    )

                    # Say that DO crossreference to the WHILE block.
                    context.operators[
                        context.operator_index
                    ].operand = block_operator.operand

                    # Say that WHILE should jump in the DO body.
                    context.operators[block_operator.operand].operand = (
                        context.operator_index + 1
                    )
                else:
                    # If invalid we call end not after the if or else.

                    # Get error location.
                    error_location = block_operator.token.location

                    # Error message.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        error_location,
                        "Error",
                        "`end` can only close `if`, `else` or `do` block!",
                        True,
                    )

                # Increment operator index.
                context.operator_index += 1
            elif current_token.value == Keyword.DEFINE:
                # This is DEFINE keyword.

                if len(reversed_tokens) == 0:
                    # No name for definition is given.

                    # Error message.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        current_token.location,
                        "Error",
                        "`define` should have name after the keyword, "
                        "do you has unfinished definition?",
                        True,
                    )

                # Get name for definition.
                definition_name = reversed_tokens.pop()

                if definition_name.type != TokenType.WORD:
                    # If name is not word.

                    # Error message.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        definition_name.location,
                        "Error",
                        "`define` name, should be of type WORD, sorry, but you can`t use something that you give as name for the definition!",
                        True,
                    )

                if definition_name.text in definitions:
                    # If already defined.

                    # Error messages.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        definition_name.location,
                        "Error",
                        "Definition with name {} was already defined!",
                        False,
                    )
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        definitions[definition_name.text].location,
                        "Error",
                        "Original definition was here...",
                        True,
                    )

                if (
                    definition_name.text in INTRINSIC_NAMES_TO_TYPE
                    or definition_name.text in KEYWORD_NAMES_TO_TYPE
                ):
                    # If default item.

                    # Error message.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        definition_name.location,
                        "Error",
                        "Can`t define definition with language defined name!",
                        True,
                    )

                # Create blank new definition.
                definition = Definition(current_token.location, [])

                # Add definition.
                definitions[definition_name.text] = definition

                # How much we require ends.
                required_end_count = 0

                while len(reversed_tokens) > 0:
                    # If there is still tokens.

                    # Get new token.
                    current_token = reversed_tokens.pop()

                    if current_token.type == TokenType.KEYWORD:
                        # If got keyword.

                        if current_token.text in KEYWORD_NAMES_TO_TYPE:
                            # If this is correct keyword.

                            if current_token.text == KEYWORD_TYPES_TO_NAME[Keyword.END]:
                                # If this is end.

                                if required_end_count <= 0:
                                    # If we no more require end.

                                    # Stop definition.
                                    break

                                # Decrease required end counter.
                                required_end_count -= 1

                            if KEYWORD_NAMES_TO_TYPE[current_token.text] in (
                                Keyword.IF,
                                Keyword.DEFINE,
                                Keyword.DO,
                            ):
                                # If this is keyword that requires end.

                                # Increase required end count.
                                required_end_count += 1

                            if (
                                KEYWORD_NAMES_TO_TYPE[current_token.text]
                                == Keyword.ELSE
                            ):
                                # If got else.

                                # Just pass as else not requires end.
                                pass
                        else:
                            # Invalid keyword.
                            assert False, "Got invalid keyword!"

                    # Append token.
                    definition.tokens.append(current_token)

                if required_end_count != 0:
                    # If there is still required end.

                    # Error message.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        current_token.location,
                        "Error",
                        f"There is {required_end_count} unclosed blocks, "
                        "that requires cloing `end` keyword inside `define` definition. ",
                        True,
                    )

                if not (
                    current_token.type == TokenType.KEYWORD
                    and current_token.text == KEYWORD_TYPES_TO_NAME[Keyword.END]
                ):
                    # If got not end at end of definition.

                    # Error message.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        current_token.location,
                        "Error",
                        "`define` should have `end` at the end of definition, "
                        "but it was not founded!",
                        True,
                    )
            else:
                # If unknown keyword type.
                assert False, "Unknown keyword type! (How?)"
        else:
            # If unknown operator type.
            assert False, "Unknown operator type! (How?)"

    if len(context.memory_stack) > 0:
        # If there is any in the stack.

        # Get error operator.
        error_operator = context.operators[context.memory_stack.pop()]

        # Get error location.
        error_location = error_operator.token.location

        # Error message.
        gofra.core.errors.message_verbosed(
            Stage.PARSER,
            error_location,
            "Error",
            f'Unclosed block "{error_operator.token.text}"!',
            True,
        )


# Source.


def load_source_from_file(file_path: str) -> Tuple[Source, ParserContext]:
    """Load file, then return ready source and context for it. (Tokenized and parsed)."""

    # Read source lines.
    source_file, _ = gofra.core.other.try_open_file(
        file_path, "r", True, encoding="UTF-8"
    )
    source_lines = source_file.readlines()
    source_file.close()

    parser_context = ParserContext()

    # Tokenize.
    lexer_tokens = list(lexer_tokenize(source_lines, file_path))

    if len(lexer_tokens) == 0:
        gofra.core.errors.message_verbosed(
            Stage.LEXER,
            (basename(file_path), 1, 1),
            "Error",
            "There is no tokens found in given file, are you given empty file?",
            True,
        )

    # Parse.
    parser_parse(lexer_tokens, parser_context, file_path)

    # Create source from context.
    parser_context_source = Source(parser_context.operators)

    return parser_context_source, parser_context


# Bytecode.


def compile_bytecode(source: Source, _, path: str):
    """Compiles operators to bytecode."""

    # Check that there is no changes in operator type or intrinsic.
    assert (
        len(OperatorType) == 10
    ), "Please update implementation for bytecode compilation after adding new OperatorType!"
    assert (
        len(Intrinsic) == 28
    ), "Please update implementation for bytecode compilation after adding new Intrinsic!"

    def __write_operator_intrinsic(operator: Operator):
        """Writes default operator (non-intrinsic)."""

        # Check that this is intrinsic operator.
        assert operator.type == OperatorType.INTRINSIC, (
            "Non-INTRINSIC operators " "should be written using __write_operator()!"
        )

        # Type check.
        assert isinstance(
            current_operator.operand, Intrinsic
        ), f"Type error, parser level error?"

        if current_operator.operand in INTRINSIC_TO_BYTECODE_OPERATOR:
            # Intristic operator.

            # Write operator data.
            write(INTRINSIC_TO_BYTECODE_OPERATOR[current_operator.operand])
        else:
            gofra.core.errors.message_verbosed(
                Stage.COMPILATOR,
                current_operator.token.location,
                "Error",
                f"Intrinsic `{INTRINSIC_TYPES_TO_NAME[current_operator.operand]}` "
                f"is not implemented for bytecode compilation!",
                True,
            )

    def __write_operator(operator: Operator, current_operator_index: int):
        """Writes default operator (non-intrinsic)."""

        # Grab our operator
        if operator.type == OperatorType.INTRINSIC:
            assert (
                False
            ), "Intrinsic operators should be written using __write_operator_intrinsic()!"
        elif operator.type == OperatorType.PUSH_INTEGER:
            assert isinstance(operator.operand, int), "Type error, parser level error?"

            # Write operator data.
            write(OPERATOR_TYPE_TO_BYTECODE_OPERATOR[OperatorType.PUSH_INTEGER])
            write(f"{operator.operand}")
        elif operator.type == OperatorType.PUSH_STRING:
            assert isinstance(operator.operand, str), "Type error, parser level error?"
            gofra.core.errors.message(
                "Error", "Strings is not implemented yet in the bytecode!", True
            )
        elif operator.type == OperatorType.IF:
            assert isinstance(
                operator.operand, OPERATOR_ADDRESS
            ), f"Type error, parser level error?"
            write("IF")
            write(f"{operator.operand}")
        elif operator.type == OperatorType.WHILE:
            assert isinstance(
                operator.operand, OPERATOR_ADDRESS
            ), f"Type error, parser level error?"
            write("WHILE")
            write(f"{operator.operand}")
        elif operator.type == OperatorType.DO:
            assert isinstance(
                operator.operand, OPERATOR_ADDRESS
            ), f"Type error, parser level error?"
            write("DO")
            write(f"{operator.operand}")
        elif operator.type == OperatorType.ELSE:
            assert isinstance(
                operator.operand, OPERATOR_ADDRESS
            ), "Type error, parser level error?"
            write("ELSE")
            write(f"{operator.operand}")
        elif operator.type == OperatorType.END:
            assert isinstance(
                operator.operand, OPERATOR_ADDRESS
            ), "Type error, parser level error?"
            write("END")
            write(f"{operator.operand}")
        elif operator.type == OperatorType.DEFINE:
            assert False, "Got definition operator at runner stage, parser level error?"
        else:
            # If unknown operator type.
            assert False, f"Got unexpected / unknon operator type! (How?)"

        # WIP.
        current_lines.append("\n")

    def write(text: str):
        """Writes text to file."""
        current_lines.append(text + " ")

    # Get source operators count.
    operators_count = len(source.operators)

    # Current operator index from the source.
    current_operator_index = 0

    # Lines.
    current_lines: List[str] = []

    # Check that there is more than zero operators in context.
    if operators_count == 0:
        # If there is no operators in the final parser context.
        gofra.core.errors.message_verbosed(
            Stage.COMPILATOR,
            (basename(path), 1, 1),
            "Error",
            "There is no operators found in given file after parsing, "
            "are you given empty file or file without resulting operators?",
            True,
        )

    # Open file.
    bytecode_path = path + ".gofbc"
    file, _ = gofra.core.other.try_open_file(bytecode_path, "w", True)

    while current_operator_index < operators_count:
        # While we not run out of the source operators list.

        # Get current operator from the source.
        current_operator: Operator = source.operators[current_operator_index]

        if current_operator.type == OperatorType.INTRINSIC:
            # If this is intrinsic.

            # Write intrinsic operator.
            __write_operator_intrinsic(current_operator)
        else:
            # If this is other operator.

            # Write default operator.
            __write_operator(current_operator, current_operator_index)

        # Increment current index.
        current_operator_index += 1

    # Write lines in final file.
    for current_stack_line in current_lines:
        file.write(current_stack_line)

    # Close file.
    file.close()
    return bytecode_path


def execute_bytecode(path: str):
    """Executes bytecode file."""

    # Check that there is no changes in operator type or intrinsic.
    assert (
        len(OperatorType) == 10
    ), "Please update implementation for bytecode execution after adding new OperatorType!"
    assert (
        len(Intrinsic) == 28
    ), "Please update implementation for bytecode execution after adding new Intrinsic!"

    if not path.endswith(".gofbc"):
        gofra.core.errors.message(
            "Error",
            f'File "{path}" should have extension `.gofbc` for being executed!',
            True,
        )
        return

    # Open file.
    file, _ = gofra.core.other.try_open_file(path, "r", True)

    # Tokenize operator tokens.
    bc_op_tokens = []
    for line in file.readlines():
        op_tokens = line.split(" ")
        for op_token in op_tokens:
            if op_token == "\n" or op_token.replace(" ", "") == "":
                continue
            bc_op_tokens.append(op_token)

    # New context.
    parser_context = ParserContext()

    # Convert OPs to interpretator operators.
    current_bc_operator_index = 0
    while current_bc_operator_index < len(bc_op_tokens):
        bc_operator = bc_op_tokens[current_bc_operator_index]
        if bc_operator == OPERATOR_TYPE_TO_BYTECODE_OPERATOR[OperatorType.PUSH_INTEGER]:
            parser_context.operators.append(
                Operator(
                    OperatorType.PUSH_INTEGER,
                    Token(TokenType.BYTECODE, bc_operator, (path, -1, -1), bc_operator),
                    int(bc_op_tokens[current_bc_operator_index + 1]),
                )
            )
            current_bc_operator_index += 2
            continue
        elif bc_operator in OPERATOR_TYPE_TO_BYTECODE_OPERATOR[OperatorType.IF]:
            parser_context.operators.append(
                Operator(
                    OperatorType.IF,
                    Token(TokenType.BYTECODE, bc_operator, (path, -1, -1), bc_operator),
                    int(bc_op_tokens[current_bc_operator_index + 1]),
                )
            )
            current_bc_operator_index += 2
            continue
        elif bc_operator == OPERATOR_TYPE_TO_BYTECODE_OPERATOR[OperatorType.END]:
            parser_context.operators.append(
                Operator(
                    OperatorType.END,
                    Token(TokenType.BYTECODE, bc_operator, (path, -1, -1), bc_operator),
                    int(bc_op_tokens[current_bc_operator_index + 1]),
                )
            )
            current_bc_operator_index += 2
            continue
        elif bc_operator == OPERATOR_TYPE_TO_BYTECODE_OPERATOR[OperatorType.ELSE]:
            parser_context.operators.append(
                Operator(
                    OperatorType.ELSE,
                    Token(TokenType.BYTECODE, bc_operator, (path, -1, -1), bc_operator),
                    int(bc_op_tokens[current_bc_operator_index + 1]),
                )
            )
            current_bc_operator_index += 2
            continue
        elif bc_operator == OPERATOR_TYPE_TO_BYTECODE_OPERATOR[OperatorType.DO]:
            parser_context.operators.append(
                Operator(
                    OperatorType.DO,
                    Token(TokenType.BYTECODE, bc_operator, (path, -1, -1), bc_operator),
                    int(bc_op_tokens[current_bc_operator_index + 1]),
                )
            )
            current_bc_operator_index += 2
            continue
        elif bc_operator == OPERATOR_TYPE_TO_BYTECODE_OPERATOR[OperatorType.WHILE]:
            parser_context.operators.append(
                Operator(
                    OperatorType.WHILE,
                    Token(TokenType.BYTECODE, bc_operator, (path, -1, -1), bc_operator),
                    int(bc_op_tokens[current_bc_operator_index + 1]),
                )
            )
            current_bc_operator_index += 2
            continue
        else:
            if bc_operator in BYTECODE_OPERATOR_NAMES_TO_INTRINSIC:
                parser_context.operators.append(
                    Operator(
                        OperatorType.INTRINSIC,
                        Token(
                            TokenType.BYTECODE, bc_operator, (path, -1, -1), bc_operator
                        ),
                        BYTECODE_OPERATOR_NAMES_TO_INTRINSIC[bc_operator],
                    )
                )
            else:
                gofra.core.errors.message_verbosed(
                    Stage.PARSER,
                    ("Bytecode", -1, -1),
                    "Error",
                    f"Got unexpected bytecode instruction - {repr(bc_operator)}!",
                    True,
                )
        current_bc_operator_index += 1
        continue

    # Run.
    bytecode_ops = []
    for operator in parser_context.operators:
        vm_bit = None
        vm_operand = None
        if operator.type == OperatorType.PUSH_INTEGER:
            vm_bit = vm.BytecodeInstructionType.STACK_PUSH_INTEGER
            vm_operand = operator.operand
        elif operator.type == OperatorType.IF:
            vm_bit = vm.BytecodeInstructionType.CONDITIONAL_IF
            vm_operand = operator.operand
        elif operator.type == OperatorType.END:
            vm_bit = vm.BytecodeInstructionType.CONDITIONAL_END
            vm_operand = operator.operand
        elif operator.type == OperatorType.ELSE:
            vm_bit = vm.BytecodeInstructionType.CONDITIONAL_ELSE
            vm_operand = operator.operand
        elif operator.type == OperatorType.DO:
            vm_bit = vm.BytecodeInstructionType.CONDITIONAL_DO
            vm_operand = operator.operand
        elif operator.type == OperatorType.WHILE:
            vm_bit = vm.BytecodeInstructionType.CONDITIONAL_WHILE
            vm_operand = operator.operand
        elif operator.type == OperatorType.INTRINSIC:
            if operator.operand == Intrinsic.SHOW:
                vm_bit = vm.BytecodeInstructionType.VM_ECHO_INTEGER
            elif operator.operand == Intrinsic.INCREMENT:
                vm_bit = vm.BytecodeInstructionType.MATH_INCREMENT
            elif operator.operand == Intrinsic.DECREMENT:
                vm_bit = vm.BytecodeInstructionType.MATH_DECREMENT
            elif operator.operand == Intrinsic.PLUS:
                vm_bit = vm.BytecodeInstructionType.MATH_ADD
            elif operator.operand == Intrinsic.MINUS:
                vm_bit = vm.BytecodeInstructionType.MATH_MINUS
            elif operator.operand == Intrinsic.MULTIPLY:
                vm_bit = vm.BytecodeInstructionType.MATH_MULTIPLY
            elif operator.operand == Intrinsic.DIVIDE:
                vm_bit = vm.BytecodeInstructionType.MATH_DIVIDE
            elif operator.operand == Intrinsic.MODULUS:
                vm_bit = vm.BytecodeInstructionType.MATH_MODULUS
            elif operator.operand == Intrinsic.COPY:
                vm_bit = vm.BytecodeInstructionType.STACK_COPY
            elif operator.operand == Intrinsic.COPY2:
                vm_bit = vm.BytecodeInstructionType.STACK_COPY2
            elif operator.operand == Intrinsic.COPY_OVER:
                vm_bit = vm.BytecodeInstructionType.STACK_COPY_OVER
            elif operator.operand == Intrinsic.FREE:
                vm_bit = vm.BytecodeInstructionType.STACK_DROP
            elif operator.operand == Intrinsic.COPY_OVER:
                vm_bit = vm.BytecodeInstructionType.STACK_SWAP
            elif operator.operand == Intrinsic.EQUAL:
                vm_bit = vm.BytecodeInstructionType.LOGIC_EQUAL
            elif operator.operand == Intrinsic.NOT_EQUAL:
                vm_bit = vm.BytecodeInstructionType.LOGIC_NOT_EQUAL
            elif operator.operand == Intrinsic.LESS_THAN:
                vm_bit = vm.BytecodeInstructionType.LOGIC_LESS
            elif operator.operand == Intrinsic.GREATER_THAN:
                vm_bit = vm.BytecodeInstructionType.LOGIC_GREATER
            elif operator.operand == Intrinsic.LESS_EQUAL_THAN:
                vm_bit = vm.BytecodeInstructionType.LOGIC_LESS_EQUAL
            elif operator.operand == Intrinsic.GREATER_EQUAL_THAN:
                vm_bit = vm.BytecodeInstructionType.LOGIC_GREATER_EQUAL
            elif operator.operand in (
                Intrinsic.MEMORY_WRITE,
                Intrinsic.MEMORY_READ,
                Intrinsic.MEMORY_WRITE4BYTES,
                Intrinsic.MEMORY_READ4BYTES,
                Intrinsic.MEMORY_SHOW_CHARACTERS,
                Intrinsic.MEMORY_POINTER,
                Intrinsic.IO_READ_INTEGER,
                Intrinsic.IO_READ_STRING,
                Intrinsic.NULL,
            ):
                vm_bit = vm.BytecodeInstructionType.MATH_MODULUS

        if vm_bit:
            bytecode_ops.append(vm.BytecodeInstruction(vm_bit, vm_operand))
            continue
        print(operator)
    vm.VM().execute_bytecode(bytecode=vm.Bytecode(bytecode_ops))

    # Close file.
    file.close()


# CLI.


def cli_validate_argument_vector(argument_vector: List[str]) -> List[str]:
    """Validates CLI argv (argument vector)"""

    # Check that ther is any in the ARGV.
    assert (
        len(argument_vector) > 0
    ), "There is no source (mspl.py) file path in the ARGV"

    # Get argument vector without source(mspl.py) path.
    argument_runner_filename: str = argument_vector[0]
    argument_vector = argument_vector[1:]

    # Validate ARGV.
    if len(argument_vector) == 0:
        # If there is no arguments.

        # Message.
        gofra.systems.cli.usage_message(argument_runner_filename)
        gofra.core.errors.message(
            "Error", "Please pass file path to work with (.gof or .gofbc ~)", True
        )
    elif len(argument_vector) == 1:
        # Just one argument.

        if argument_vector[0] != "help":
            # If this is not help.

            # Message.
            gofra.systems.cli.usage_message(argument_runner_filename)
            gofra.core.errors.message(
                "Error", "Please pass subcommand after the file path!", True
            )

        # Show usage.
        gofra.systems.cli.usage_message(argument_runner_filename)

        # Exit.
        exit(0)

        # Return path as source file and help (argv[0]).
        return ["", argument_vector[0], ""]
    elif len(argument_vector) == 2:
        # Expected ARGV length.

        # All ok.
        return [*argument_vector, ""]
    elif len(argument_vector) == 3:
        # If this is may silent argument.

        if argument_vector[2] != "-silent":
            # If silent.

            # Message.
            gofra.systems.cli.usage_message(argument_runner_filename)
            gofra.core.errors.message("Error", "Unexpected arguments!", True)

    # Return final ARGV.
    return argument_vector


def cli_entry_point():
    """Entry point for the CLI."""

    # Get and check size of cli argument vector.
    cli_argument_vector = cli_validate_argument_vector(argv)
    assert len(cli_argument_vector) == 3, "Got unexpected size of argument vector."

    # CLI Options.
    cli_source_path, cli_subcommand, cli_silent = cli_argument_vector
    cli_silent = bool(cli_silent == "-silent")

    # Welcome message.
    if not cli_silent:
        gofra.systems.cli.welcome_message()

    # Load source and check size of it.
    loaded_file = None
    if cli_subcommand in ("run", "dump", "compile"):
        loaded_file = load_source_from_file(cli_source_path)
        assert len(loaded_file) == 2, "Got unexpected data from loaded file."

    if cli_subcommand == "run":
        cli_source, cli_context = loaded_file
        bytecode_path = compile_bytecode(cli_source, cli_context, cli_source_path)
        if not cli_silent:
            print(
                f'[Info] Generated bytecode for "{basename(cli_source_path)}" in to the file "{basename(bytecode_path)}"!'
            )

        execute_bytecode(bytecode_path)
        if not cli_silent:
            print(f'[Info] Bytecode file "{basename(bytecode_path)}" was executed!')
    elif cli_subcommand == "dump":
        cli_source, _ = loaded_file
        gofra.systems.dump.dump(cli_source.operators)
        if not cli_silent:
            print(f'[Info] File "{basename(cli_source_path)}" was dump printed!')
    elif cli_subcommand == "compile":
        cli_source, cli_context = loaded_file
        bytecode_path = compile_bytecode(cli_source, cli_context, cli_source_path)
        if not cli_silent:
            print(
                f'[Info] Generated bytecode for "{basename(cli_source_path)}" in to the file "{basename(bytecode_path)}"!'
            )
    elif cli_subcommand == "execute":
        execute_bytecode(cli_source_path)
        if not cli_silent:
            print(f'[Info] Bytecode file "{basename(bytecode_path)}" was executed!')
    else:
        gofra.systems.cli.usage_message(__file__)
        gofra.core.errors.message("Error", f"Unknown subcommand `{cli_subcommand}`!")


if __name__ == "__main__":
    cli_entry_point()
