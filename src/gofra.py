"""
    Main Gofra programming language source code.

"""

__author__ = "Kirill Zhosul @kirillzhosul"
__license__ = "MIT"

from typing import Generator
from os.path import basename
from sys import argv

import gofra
from gofra.core.danger import *
from gofra.core.stack import Stack


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
    assert len(Keyword) == 8, "Please update implementation after adding new Keyword!"

    # Check that there is no changes in token type.
    assert (
        len(TokenType) == 6
    ), "Please update implementation after adding new TokenType!"

    # Reverse tokens.
    reversed_tokens: List[Token] = list(reversed(tokens))

    # Definitions.
    definitions: Dict[str, Definition] = dict()
    memories: Dict[str, Memory] = dict()
    variables: Dict[str, Variable] = dict()
    variables_offset = 0
    memories_offset = 0

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

            if current_token.text in memories:
                memory = memories[current_token.text]
                context.operators.append(
                    Operator(
                        type=OperatorType.PUSH_INTEGER,
                        token=current_token,
                        operand=memory.ptr_offset,
                    )
                )
                context.operator_index += 1
                continue

            if current_token.text in variables:
                variable = variables[current_token.text]
                context.operators.append(
                    Operator(
                        type=OperatorType.PUSH_INTEGER,
                        token=current_token,
                        operand=variable.ptr_offset,
                    )
                )
                context.operator_index += 1
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
            elif current_token.value == Keyword.MEMORY:
                if len(reversed_tokens) == 0:
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        current_token.location,
                        "Error",
                        "`memory` should have name after the keyword, "
                        "do you has unfinished memory definition?",
                        True,
                    )

                name_token = reversed_tokens.pop()

                if name_token.type != TokenType.WORD:
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        name_token.location,
                        "Error",
                        "`memory` name, should be of type WORD, sorry, but "
                        "you can`t use something that you give as name "
                        "for the memory!",
                        True,
                    )

                if name_token.text in memories or name_token.text in definitions:
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        name_token.location,
                        "Error",
                        f"Definition or memory with name {name_token.text} "
                        f"was already defined!",
                        False,
                    )
                    if name_token.text in definitions:
                        gofra.core.errors.message_verbosed(
                            Stage.PARSER,
                            definitions[name_token.text].location,
                            "Error",
                            "Original definition was here...",
                            True,
                        )
                    # TODO: Memory location report.

                if (
                    name_token.text in INTRINSIC_NAMES_TO_TYPE
                    or name_token.text in KEYWORD_NAMES_TO_TYPE
                ):
                    # If default item.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        name_token.location,
                        "Error",
                        "Can`t define memories with language defined name!",
                        True,
                    )

                if len(reversed_tokens) <= 0:
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        name_token.location,
                        "Error",
                        "`memory` requires size for memory definition, "
                        "which was not given!",
                        True,
                    )
                memory_size_token = reversed_tokens.pop()

                if memory_size_token.type != TokenType.INTEGER:
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        name_token.location,
                        "Error",
                        "`var` size, should be of type INTEGER, sorry, but "
                        "you can`t use something that you give as size "
                        "for the memory!",
                        True,
                    )
                # TODO: Proper evaluation.

                # Create blank new memory.
                memory_name = name_token.text
                memories[memory_name] = Memory(
                    memory_name, memory_size_token.value, memories_offset
                )
                memories_offset += memory_size_token.value

                if len(reversed_tokens) >= 0:
                    end_token = reversed_tokens.pop()
                    if (
                        end_token.type == TokenType.KEYWORD
                        and end_token.text == KEYWORD_TYPES_TO_NAME[Keyword.END]
                    ):
                        continue

                # If got not end at end of definition.
                gofra.core.errors.message_verbosed(
                    Stage.PARSER,
                    current_token.location,
                    "Error",
                    "`memory` should have `end` at the end of memory definition, "
                    "but it was not founded!",
                    True,
                )
            elif current_token.value == Keyword.VARIABLE:
                if len(reversed_tokens) == 0:
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        current_token.location,
                        "Error",
                        "`var` should have name after the keyword, "
                        "do you has unfinished variable definition?",
                        True,
                    )

                name_token = reversed_tokens.pop()

                if name_token.type != TokenType.WORD:
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        name_token.location,
                        "Error",
                        "`var` name, should be of type WORD, sorry, but "
                        "you can`t use something that you give as name "
                        "for the variable!",
                        True,
                    )

                if (
                    name_token.text in variables
                    or name_token.text in definitions
                    or name_token.text in memories
                ):
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        name_token.location,
                        "Error",
                        f"Definition or variable with name {name_token.text} "
                        f"was already defined!",
                        False,
                    )
                    if name_token.text in definitions:
                        gofra.core.errors.message_verbosed(
                            Stage.PARSER,
                            definitions[name_token.text].location,
                            "Error",
                            "Original definition was here...",
                            True,
                        )
                    # TODO: Memory / variable location report.

                if (
                    name_token.text in INTRINSIC_NAMES_TO_TYPE
                    or name_token.text in KEYWORD_NAMES_TO_TYPE
                ):
                    # If default item.
                    gofra.core.errors.message_verbosed(
                        Stage.PARSER,
                        name_token.location,
                        "Error",
                        "Can`t define variable with language defined name!",
                        True,
                    )
                # Create blank new memory.
                variable_name = name_token.text
                variables[variable_name] = Variable(variable_name, variables_offset)
                variables_offset += VARIABLE_SIZE
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


# Interpretator.


def interpretator_run(source: Source, bytearray_size: int = MEMORY_BYTEARRAY_SIZE):
    """Interpretates the source."""
    assert (
        len(OperatorType) == 10
    ), "Please update implementation after adding new OperatorType!"
    assert (
        len(Intrinsic) == 30
    ), "Please update implementation after adding new Intrinsic!"

    # Create empty stack.
    memory_execution_stack = Stack()

    # String pointers.
    memory_string_pointers: Dict[OPERATOR_ADDRESS, TYPE_POINTER] = dict()
    memory_string_size = bytearray_size
    memory_string_size_ponter = 0

    # Allocate sized bytearray.
    memory_bytearray = bytearray(
        bytearray_size
        + memory_string_size
        + MEMORY_MEMORIES_SIZE
        + MEMORY_VARIABLES_SIZE
    )

    # Get source operators count.
    operators_count = len(source.operators)

    current_operator_index = 0

    if operators_count == 0:
        gofra.core.errors.message_verbosed(
            Stage.RUNNER,
            ("__RUNNER__", 1, 1),
            "Error",
            "There is no operators found in given file after parsing, "
            "are you given empty file or file without resulting operators?",
            True,
        )

    while current_operator_index < operators_count:
        # While we not run out of the source operators list.

        # Get current operator from the source.
        current_operator: Operator = source.operators[current_operator_index]

        try:
            # Try / Catch to get unexpected Python errors.

            if current_operator.type == OperatorType.PUSH_INTEGER:
                # Push integer operator.

                # Type check.
                assert isinstance(
                    current_operator.operand, int
                ), "Type error, parser level error?"

                # Push operand to the stack.
                memory_execution_stack.push(current_operator.operand)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.type == OperatorType.PUSH_STRING:
                # Push string operator.

                # Type check.
                assert isinstance(
                    current_operator.operand, str
                ), "Type error, parser level error?"

                # Get string data.
                string_value = current_operator.operand.encode("UTF-8")
                string_length = len(string_value)

                if current_operator_index not in memory_string_pointers:
                    # If we not found string in allocated string pointers.

                    # Get pointer, and push in to the pointers.
                    string_pointer: TYPE_POINTER = (
                        memory_string_size + 1 + memory_string_size_ponter
                    )
                    memory_string_pointers[current_operator_index] = string_pointer

                    # Write string right into the bytearray memory.
                    memory_bytearray[
                        string_pointer : string_pointer + string_length
                    ] = string_value

                    # Increase next pointer by current string length.
                    memory_string_size_ponter += string_length

                    # Check that there is no overflow.
                    if string_length > memory_string_size:
                        # If overflowed.

                        # Error.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            "Trying to push string, when there is memory string buffer overflow!"
                            " Try use memory size directive, to increase size!",
                            True,
                        )

                # Push found string pointer to the stack.
                found_string_pointer = memory_string_pointers[current_operator_index]
                memory_execution_stack.push(found_string_pointer)

                # Push string length to the stack.
                memory_execution_stack.push(string_length)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.type == OperatorType.INTRINSIC:
                # Intrinsic operator.

                if current_operator.operand == Intrinsic.PLUS:
                    # Intristic plus operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push sum to the stack.
                    memory_execution_stack.push(operand_b + operand_a)
                elif current_operator.operand == Intrinsic.DIVIDE:
                    # Intristic divide operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push divide to the stack.
                    memory_execution_stack.push(operand_b // operand_a)
                elif current_operator.operand == Intrinsic.MODULUS:
                    # Intristic modulus operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push divide to the stack.
                    memory_execution_stack.push(int(operand_b % operand_a))
                elif current_operator.operand == Intrinsic.MINUS:
                    # Intristic minus operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push difference to the stack.
                    memory_execution_stack.push(operand_b - operand_a)
                elif current_operator.operand == Intrinsic.MULTIPLY:
                    # Intristic multiply operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push muliply to the stack.
                    memory_execution_stack.push(operand_b * operand_a)
                elif current_operator.operand == Intrinsic.EQUAL:
                    # Intristic equal operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push equal to the stack.
                    memory_execution_stack.push(int(operand_b == operand_a))
                elif current_operator.operand == Intrinsic.NOT_EQUAL:
                    # Intristic not equal operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push not equal to the stack.
                    memory_execution_stack.push(int(operand_b != operand_a))
                elif current_operator.operand == Intrinsic.LESS_THAN:
                    # Intristic less than operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push less than to the stack.
                    memory_execution_stack.push(int(operand_b < operand_a))
                elif current_operator.operand == Intrinsic.GREATER_THAN:
                    # Intristic greater than operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push greater than to the stack.
                    memory_execution_stack.push(int(operand_b > operand_a))
                elif current_operator.operand == Intrinsic.LESS_EQUAL_THAN:
                    # Intristic less equal than operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push less equal than to the stack.
                    memory_execution_stack.push(int(operand_b <= operand_a))
                elif current_operator.operand == Intrinsic.GREATER_EQUAL_THAN:
                    # Intristic greater equal than operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push greater equal than to the stack.
                    memory_execution_stack.push(int(operand_b >= operand_a))
                elif current_operator.operand == Intrinsic.SWAP:
                    # Intristic swap operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push swapped to the stack.
                    memory_execution_stack.push(operand_a)
                    memory_execution_stack.push(operand_b)
                elif current_operator.operand == Intrinsic.COPY:
                    # Intristic copy operator.

                    # Get operand.
                    operand_a = memory_execution_stack.pop()

                    # Push copy to the stack.
                    memory_execution_stack.push(operand_a)
                    memory_execution_stack.push(operand_a)
                elif current_operator.operand == Intrinsic.COPY2:
                    # Intristic copy2 operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push copy to the stack.
                    memory_execution_stack.push(operand_b)
                    memory_execution_stack.push(operand_a)
                    memory_execution_stack.push(operand_b)
                    memory_execution_stack.push(operand_a)
                elif current_operator.operand == Intrinsic.COPY_OVER:
                    # Intristic copy over operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push copy to the stack.
                    memory_execution_stack.push(operand_b)
                    memory_execution_stack.push(operand_a)
                    memory_execution_stack.push(operand_b)
                elif current_operator.operand == Intrinsic.DECREMENT:
                    # Intristic decrement operator.

                    # Get operand.
                    operand_a = memory_execution_stack.pop()

                    # Push decrement to the stack.
                    memory_execution_stack.push(operand_a - 1)
                elif current_operator.operand == Intrinsic.INCREMENT:
                    # Intristic increment operator.

                    # Get operand.
                    operand_a = memory_execution_stack.pop()

                    # Push increment to the stack.
                    memory_execution_stack.push(operand_a + 1)
                elif current_operator.operand == Intrinsic.FREE:
                    # Intristic free operator.

                    # Pop and left.
                    memory_execution_stack.pop()
                elif current_operator.operand == Intrinsic.SHOW:
                    # Intristic show operator.

                    # Get operand.
                    operand_a = memory_execution_stack.pop()

                    # Show operand.
                    print(operand_a)
                elif current_operator.operand == Intrinsic.MEMORY_WRITE:
                    # Intristic memory write operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    if operand_b > len(memory_bytearray):
                        # If this is going to be memory overflow.

                        # Error.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Trying to write at memory address {operand_b} "
                            f"that overflows memory buffer size {(len(memory_bytearray))}"
                            " bytes (MemoryBufferOverflow)",
                            True,
                        )
                    elif operand_b < 0:
                        # If this is going to be memory undeflow.

                        # Error.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Trying to write at memory address {operand_b} "
                            f"that underflows memory buffer size {(len(memory_bytearray))}"
                            " bytes (MemoryBufferUnderflow)",
                            True,
                        )

                    # Write memory.
                    try:
                        memory_bytearray[operand_b] = operand_a
                    except IndexError:
                        # Memory error.

                        # Error message.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Memory buffer (over|under)flow "
                            f"(Write to pointer {operand_b} when there is memory buffer "
                            f"with size {len(memory_bytearray)} bytes)!",
                            True,
                        )

                    except ValueError:
                        # If this is 8bit (1byte) range (number) overflow.

                        # Error message.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Memory buffer cell can only contain 1 byte (8 bit) "
                            f"that must be in range (0, 256),\nbut you passed number "
                            f"{operand_a} which is not fits in the 1 byte cell! (ByteOverflow)",
                            True,
                        )
                elif current_operator.operand == Intrinsic.MEMORY_WRITE4BYTES:
                    # Intristic memory write 4 bytes operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Convert value to 4 bytes.
                    try:
                        operand_a = operand_a.to_bytes(
                            length=4, byteorder="little", signed=(operand_a < 0)
                        )
                    except OverflowError:
                        # Error message.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Memory buffer cell can only contain 4 byte (32 bit) "
                            f"that must be in range (0, 4294967295),\nbut you passed number "
                            f"{operand_a} which is not fits in the 4 byte cell! (ByteOverflow)",
                            True,
                        )

                    if operand_b + 4 - 1 > len(memory_bytearray):
                        # If this is going to be memory overflow.

                        # Error.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Trying to write 4 bytes to memory address from {operand_b} to "
                            f"{operand_b + 4 - 1} "
                            f"that overflows memory buffer size {(len(memory_bytearray))}"
                            " bytes (MemoryBufferOverflow)",
                            True,
                        )
                    elif operand_b < 0:
                        # If this is going to be memory undeflow.

                        # Error.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Trying to write at memory address "
                            f"from {operand_b} to {operand_b + 2} "
                            f"that underflows memory buffer size {(len(memory_bytearray))}"
                            " bytes (MemoryBufferUnderflow)",
                            True,
                        )

                    # Write memory.
                    try:
                        memory_bytearray[operand_b : operand_b + 4] = operand_a
                    except IndexError:
                        # Memory* error.

                        # Error message.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Memory buffer (over|under)flow "
                            f"(Write to pointer from "
                            f"{operand_b} to {operand_b + 4 - 1} "
                            f"when there is memory buffer with size "
                            f"{len(memory_bytearray)} bytes)!",
                            True,
                        )

                    except ValueError:
                        # If this is 32bit (4byte) range (number) overflow.

                        # Error message.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Memory buffer cell can only contain 4 byte (32 bit) "
                            f"that must be in range (0, 4294967295),\nbut you passed number "
                            f"{operand_a} which is not fits in the 4 byte cell! (ByteOverflow)",
                            True,
                        )
                elif current_operator.operand == Intrinsic.MEMORY_READ4BYTES:
                    # Intristic memory read 4 bytes operator.

                    # Get operand.
                    operand_a = memory_execution_stack.pop()

                    if operand_a + 4 - 1 > len(memory_bytearray):
                        # If this is going to be memory overflow.

                        # Error.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Trying to read from memory address "
                            f"{operand_a} to {operand_a + 4 - 1} "
                            f"that overflows memory buffer size {(len(memory_bytearray))}"
                            " bytes (MemoryBufferOverflow)",
                            True,
                        )
                    elif operand_a < 0:
                        # If this is going to be memory undeflow.

                        # Error.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Trying to read from memory address "
                            f"{operand_a} to {operand_a + 4 - 1}"
                            f"that underflows memory buffer size {(len(memory_bytearray))}"
                            " bytes (MemoryBufferUnderflow)",
                            True,
                        )
                    # Read memory at the pointer.
                    try:
                        memory_bytes = int.from_bytes(
                            memory_bytearray[operand_a : operand_a + 4],
                            byteorder="little",
                        )
                    except IndexError:
                        # Memory* error.

                        # Error message.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Memory buffer (over|under)flow "
                            f"(Read from pointer {operand_a} to {operand_a + 4 - 1} "
                            f"when there is memory buffer with size "
                            f"{len(memory_bytearray)} bytes)!",
                            True,
                        )
                    else:
                        # Push memory to the stack.
                        memory_execution_stack.push(memory_bytes)
                elif current_operator.operand == Intrinsic.MEMORY_READ:
                    # Intristic memory read operator.

                    # Get operand.
                    operand_a = memory_execution_stack.pop()

                    if operand_a > len(memory_bytearray):
                        # If this is going to be memory overflow.

                        # Error.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Trying to read from memory address {operand_a} "
                            f"that overflows memory buffer size {(len(memory_bytearray))}"
                            " bytes (MemoryBufferOverflow)",
                            True,
                        )
                    elif operand_a < 0:
                        # If this is going to be memory undeflow.

                        # Error.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Trying to read from memory address {operand_a} "
                            f"that underflows memory buffer size {(len(memory_bytearray))}"
                            " bytes (MemoryBufferUnderflow)",
                            True,
                        )
                    # Read memory at the pointer.
                    try:
                        memory_byte = memory_bytearray[operand_a]
                    except IndexError:
                        # Memory* error.

                        # Error message.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Memory buffer (over|under)flow "
                            f"(Read from pointer {operand_a} when there is memory buffer "
                            f"with size {len(memory_bytearray)} bytes)!",
                            True,
                        )
                    else:
                        # Push memory to the stack.
                        memory_execution_stack.push(memory_byte)
                elif current_operator.operand == Intrinsic.MEMORY_SHOW_CHARACTERS:
                    # Intristic memory show as chars operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # String to show.
                    memory_string: bytes = b""

                    if operand_b + operand_a > len(memory_bytearray):
                        # If this is going to be memory overflow.

                        # Error.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Trying to read from memory address "
                            f"from {operand_b} to {operand_b + operand_a} "
                            f"that overflows memory buffer size {(len(memory_bytearray))}"
                            " bytes (MemoryBufferOverflow)",
                            True,
                        )
                    elif operand_a < 0:
                        # If this is going to be memory undeflow.

                        # Error.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Trying to read from memory address"
                            f"from {operand_b} to {operand_b + operand_a} "
                            f"that underflows memory buffer size {(len(memory_bytearray))}"
                            " bytes (MemoryBufferUnderflow)",
                            True,
                        )

                    # Read memory string.
                    try:
                        memory_string = memory_bytearray[
                            operand_b : operand_b + operand_a
                        ]
                    except IndexError:
                        # Memory* error.

                        # Error message.
                        gofra.core.errors.message_verbosed(
                            Stage.RUNNER,
                            current_operator.token.location,
                            "Error",
                            f"Memory buffer (over|under)flow "
                            f"(Read from {operand_b} to {operand_b + operand_a} "
                            f"when there is memory "
                            f"buffer with size {len(memory_bytearray)} bytes)!",
                            True,
                        )

                    # Print decoded memory bytes.
                    print(memory_string.decode("UTF-8"), end="")
                elif current_operator.operand == Intrinsic.MEMORY_POINTER:
                    # Intristic memory pointer operator.

                    # Push pointer to the stack.
                    memory_execution_stack.push(MEMORY_BYTEARRAY_NULL_POINTER)
                elif current_operator.operand == Intrinsic.NULL:
                    # Intristic null operator.

                    # Push pointer to the stack.
                    memory_execution_stack.push(0)
                elif current_operator.operand == Intrinsic.IO_READ_STRING:
                    # Intrinsic I/O read string operator.

                    # Get string data.
                    string_value = input().encode("UTF-8")
                    string_length = len(string_value)

                    if current_operator_index not in memory_string_pointers:
                        # If we not found string in allocated string pointers.

                        # Get pointer, and push in to the pointers.
                        string_pointer: TYPE_POINTER = 1 + memory_string_size_ponter
                        memory_string_pointers[current_operator_index] = string_pointer

                        # Write string right into the bytearray memory.
                        memory_bytearray[
                            string_pointer : string_pointer + string_length
                        ] = string_value

                        # Increase next pointer by current string length.
                        memory_string_size_ponter += string_length

                        # Check that there is no overflow.
                        if string_length > memory_string_size:
                            # If overflow.

                            # Error.
                            gofra.core.errors.message_verbosed(
                                Stage.RUNNER,
                                current_operator.token.location,
                                "Error",
                                "Trying to push I/O string, "
                                "when there is memory string buffer overflow! "
                                "Try use memory size directive, to increase size!",
                                True,
                            )

                    # Push found string pointer to the stack.
                    found_string_pointer = memory_string_pointers[
                        current_operator_index
                    ]
                    memory_execution_stack.push(found_string_pointer)

                    # Push string length to the stack.
                    memory_execution_stack.push(string_length)
                elif current_operator.operand == Intrinsic.IO_READ_INTEGER:
                    # Intrinsic I/O read integer operator.

                    # Get integer data.
                    try:
                        integer_value = int(input())
                    except ValueError:
                        integer_value = -1

                    # Push integer to the stack.
                    memory_execution_stack.push(integer_value)
                else:
                    # If unknown instrinsic type.
                    assert False, "Unknown instrinsic! (How?)"

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.type == OperatorType.IF:
                # IF operator.

                # Get operand.
                operand_a = memory_execution_stack.pop()

                # Type check.
                assert isinstance(
                    current_operator.operand, OPERATOR_ADDRESS
                ), "Type error, parser level error?"

                if operand_a == 0:
                    # If this is false.

                    # Type check.
                    assert isinstance(
                        current_operator.operand, OPERATOR_ADDRESS
                    ), "Type error, parser level error?"

                    # Jump to the operator operand.
                    # As this is IF, so we should jump to the END.
                    current_operator_index = current_operator.operand
                else:
                    # If this is true.

                    # Increment operator index.
                    # This is makes jump into the if branch.
                    current_operator_index += 1
            elif current_operator.type == OperatorType.ELSE:
                # ELSE operator.

                # Type check.
                assert isinstance(
                    current_operator.operand, OPERATOR_ADDRESS
                ), "Type error, parser level error?"

                # Jump to the operator operand.
                # As this is ELSE operator, we should have index + 1, index!
                current_operator_index = current_operator.operand
            elif current_operator.type == OperatorType.DO:
                # DO operator.

                # Get operand.
                operand_a = memory_execution_stack.pop()

                # Type check.
                assert isinstance(
                    current_operator.operand, OPERATOR_ADDRESS
                ), "Type error, parser level error?"

                if operand_a == 0:
                    # If this is false.

                    # Endif jump operator index.
                    end_jump_operator_index = source.operators[
                        current_operator.operand
                    ].operand

                    # Type check.
                    assert isinstance(
                        end_jump_operator_index, OPERATOR_ADDRESS
                    ), "Type error, parser level error?"

                    # Jump to the operator operand.
                    # As this is DO, so we should jump to the END.
                    current_operator_index = int(end_jump_operator_index)
                else:
                    # If this is true.

                    # Increment operator index.
                    # This is makes jump into the if body.
                    current_operator_index += 1
            elif current_operator.type == OperatorType.WHILE:
                # WHILE operator.

                # Increment operator index.
                # This is makes jump into the if statement (expression).
                current_operator_index += 1
            elif current_operator.type == OperatorType.END:
                # END operator.

                # Type check.
                assert isinstance(
                    current_operator.operand, OPERATOR_ADDRESS
                ), "Type error, parser level error?"

                # Type check.
                assert isinstance(
                    current_operator.operand, OPERATOR_ADDRESS
                ), "Type error, parser level error?"

                # Jump to the operator operand.
                # As this is END operator, we should have index + 1, index!
                current_operator_index = current_operator.operand
            elif current_operator.type == OperatorType.DEFINE:
                # DEFINE Operator.

                # Error.
                assert (
                    False
                ), "Got definition operator at runner stage, parser level error?"
            elif current_operator.type == OperatorType.MEMORY:
                assert False, "Got memory operator at runner stage, parser level error?"
            else:
                # If unknown operator type.
                assert False, "Unknown operator type! (How?)"
        except IndexError:
            # Should be stack error.

            # Error message.
            gofra.core.errors.message_verbosed(
                Stage.RUNNER,
                current_operator.token.location,
                "Error",
                f"Stack error! This is may caused by popping from empty stack!"
                f"IndexError, (From: {current_operator.token.text})",
                True,
            )
        except KeyboardInterrupt:
            # If stopped.

            # Error message.
            gofra.core.errors.message_verbosed(
                Stage.RUNNER,
                current_operator.token.location,
                "Error",
                "Interpretation was stopped by keyboard interrupt!",
                True,
            )

    if len(memory_execution_stack) > 0:
        # If there is any in the stack.

        # Error message.
        gofra.core.errors.message_verbosed(
            Stage.RUNNER,
            ("__runner__", 1, 1),
            "Warning",
            "Stack is not empty after running the interpretation!",
        )


# Source.


def load_source_from_file(file_path: str) -> tuple[Source, ParserContext]:
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

    def __write_operator(operator: Operator):
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
            gofra.core.errors.message(
                "Error", "Conditional is not implemented yet in the bytecode!", True
            )
        elif operator.type == OperatorType.WHILE:
            assert isinstance(
                operator.operand, OPERATOR_ADDRESS
            ), f"Type error, parser level error?"
            gofra.core.errors.message(
                "Error", "Conditional is not implemented yet in the bytecode!", True
            )
        elif operator.type == OperatorType.DO:
            assert isinstance(
                operator.operand, OPERATOR_ADDRESS
            ), f"Type error, parser level error?"
            gofra.core.errors.message(
                "Error", "Conditional is not implemented yet in the bytecode!", True
            )
        elif operator.type == OperatorType.ELSE:
            assert isinstance(
                operator.operand, OPERATOR_ADDRESS
            ), "Type error, parser level error?"
            gofra.core.errors.message(
                "Error", "Conditional is not implemented yet in the bytecode!", True
            )
        elif operator.type == OperatorType.END:
            assert isinstance(
                operator.operand, OPERATOR_ADDRESS
            ), "Type error, parser level error?"
            gofra.core.errors.message(
                "Error", "Conditional is not implemented yet in the bytecode!", True
            )
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
            __write_operator(current_operator)

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
    parser_context_source = Source(parser_context.operators)
    interpretator_run(parser_context_source)

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
    cli_silent: bool = bool(cli_silent == "-silent")

    # Welcome message.
    if not cli_silent:
        gofra.systems.cli.welcome_message()

    # Load source and check size of it.
    loaded_file = None
    if cli_subcommand in ("run", "graph", "dump", "compile"):
        loaded_file = load_source_from_file(cli_source_path)
        assert len(loaded_file) == 2, "Got unexpected data from loaded file."

    if cli_subcommand == "run":
        # If this is interpretate subcommand.

        cli_source, cli_context = loaded_file

        interpretator_run(cli_source, cli_context.memory_bytearray_size)

        # Message.
        if not cli_silent:
            print(f'[Info] File "{basename(cli_source_path)}" was interpreted!')
    elif cli_subcommand == "graph":
        # If this is graph subcommand.

        # Get source from loaded file.
        cli_source, _ = loaded_file

        # Generate graph file.
        gofra.systems.graph.write(cli_source, cli_source_path)

        # Message.
        if not cli_silent:
            print(f'[Info] .dot file "{basename(cli_source_path)}.dot" generated!')
    elif cli_subcommand == "dump":
        # If this is dump subcommand.

        # Get source from loaded file.
        cli_source, _ = loaded_file

        # Dump print.
        gofra.systems.dump.dump(cli_source.operators)

        # Message.
        if not cli_silent:
            print(f'[Info] File "{basename(cli_source_path)}" was dump printed!')
    elif cli_subcommand == "compile":
        # If this is compile subcommand.

        # Get source from loaded file.
        cli_source, cli_context = loaded_file

        # Compile.
        bytecode_path = compile_bytecode(cli_source, cli_context, cli_source_path)

        # Message.
        if not cli_silent:
            print(
                f'[Info] File "{basename(cli_source_path)}" was compiled to "{basename(bytecode_path)}"!'
            )
    elif cli_subcommand == "execute":
        # If this is execute subcommand.

        # Execute.
        execute_bytecode(cli_source_path)

        # Message.
        if not cli_silent:
            print(f'[Info] File "{basename(cli_source_path)}" was executed!')
    else:
        # If unknown subcommand.

        # Message.
        gofra.systems.cli.usage_message(__file__)
        gofra.core.errors.message("Error", f"Unknown subcommand `{cli_subcommand}`!")


if __name__ == "__main__":
    cli_entry_point()
