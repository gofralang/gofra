# MSPL Source Code.
# "Most Simple|Stupid Programming Language".

# Dataclass.
from dataclasses import dataclass, field

# System error.
from sys import stderr

# Current working directory and basename.
from os import getcwd
from os.path import basename

# Enum for types.
from enum import IntEnum, Enum, auto

# Typing for type hints.
from typing import Optional, Union, Tuple, List, Dict, Callable, Generator


class DataType(IntEnum):
    """ Enumeration for datatype types. """
    INTEGER = auto()


class Keyword(Enum):
    """ Enumeration for keyword types. """

    # Conditions.
    IF = auto()
    ENDIF = auto()


class Intrinsic(Enum):
    """ Enumeration for intrinsic types. """

    # Int.
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()

    # Boolean.
    EQUAL = auto()
    NOT_EQUAL = auto()

    # Stack.
    COPY = auto()
    FREE = auto()

    # Utils.
    SHOW = auto()


class TokenType(Enum):
    """ Enumeration for token types. """
    INTEGER = auto()
    WORD = auto()
    KEYWORD = auto()


class OperatorType(Enum):
    """ Enumeration for operaror types. """
    PUSH_INTEGER = auto()
    INTRINSIC = auto()

    # Conditions.
    IF = auto()
    ENDIF = auto()


# Types.

# Operand.
OPERAND = Optional[Union[int, Intrinsic]]

# Location.
LOCATION = Tuple[str, int, int]

# Value.
VALUE = Union[int, str, Keyword]

# Adress to the another operator.
OPERATOR_ADDRESS = int

# Other.

# Intrinsic names / types.
assert len(Intrinsic) == 8, "Please update INTRINSIC_NAMES_TO_TYPE after adding new Intrinsic!"
INTRINSIC_NAMES_TO_TYPE: Dict[str, Intrinsic] = {
    "+": Intrinsic.PLUS,
    "-": Intrinsic.MINUS,
    "*": Intrinsic.MULTIPLY,
    "==": Intrinsic.EQUAL,
    "!=": Intrinsic.NOT_EQUAL,
    "show": Intrinsic.SHOW,
    "copy": Intrinsic.COPY,
    "free": Intrinsic.FREE
}
INTRINSIC_TYPES_TO_NAME: Dict[Intrinsic, str] = {
    value: key for key, value in INTRINSIC_NAMES_TO_TYPE.items()
}

# Keyword names / types.
assert len(Keyword) == 2, "Please update KEYWORD_NAMES_TO_TYPE after adding new Keyword!"
KEYWORD_NAMES_TO_TYPE: Dict[str, Keyword] = {
    "if": Keyword.IF,
    "endif": Keyword.ENDIF,
}


@dataclass
class Token:
    """ Token dataclass implementation """

    # Type of the token.
    type: TokenType

    # Text of the token.
    text: str

    # Location of the token.
    location: LOCATION

    # Value of the token.
    value: VALUE


@dataclass
class Operator:
    """ Operator dataclass implementation. """

    # Type of the operator.
    type: OperatorType

    # Token of the operator.
    token: Token

    # Operand of the operator.
    operand: OPERAND = None


@dataclass
class Source:
    """ Program dataclass implementation. """

    operators: List[Operator] = field(default_factory=list)


@dataclass
class ParserContext:
    """ Parser context dataclass implementation. """

    # Context.
    operators: List[Operator] = field(default_factory=list)

    # Memory stack.
    memory_stack: List[OPERATOR_ADDRESS] = field(default_factory=list)

    # Current parsing operator index.
    operator_index: OPERATOR_ADDRESS = 0


# Other.

def error_message(location: LOCATION, level: str, text: str):
    """ Shows error message. """

    # Container with data.
    container = (level, *location, text)

    # Message.
    print("[%s] (%s) on %d:%d - %s" % container, file=stderr)


def no_arguments_error_message(operator: Operator):
    """ Shows no arguments passed error message. """

    if operator.type == OperatorType.INTRINSIC:
        # Intrinsic Operator.

        # Type check.
        assert isinstance(operator.operand, Intrinsic), "Type error, parser level error?"

        # Error
        error_message(operator.token.location, "Error",
                      f"`{INTRINSIC_TYPES_TO_NAME[operator.operand]}` "
                      f"intrinsic should have more arguments at the stack, but it was not founded!")

    elif operator.type == OperatorType.IF:
        # IF Operator.

        # Error
        error_message(operator.token.location, "Error",
                      "`IF` operator should have 1 argument at the stack, but it was not found!")
    else:
        # Unknown operator.
        assert False, "Tried to call no_arguments_error_message() " \
                      "for operator that does not need arguments! (Type checker error?)"


# Lexer.

def lexer_find_collumn(line: str, start: int, predicate_function: Callable[[str], bool]) -> int:
    """ Finds column in the line from start that not triggers filter. """

    # Get end position.
    end = len(line)

    while start < end and not predicate_function(line[start]):
        # While we dont reach end or not trigger predicate function.

        # Increment start.
        start += 1

    # Return counter.
    return start


def lexer_tokenize(lines: List[str], file_parent: str) -> Generator[Token, None, None]:
    """ Tokenizes lines into list of the Tokens. """

    # Get the basename.
    file_parent = basename(file_parent)

    # Check that there is no changes in token type.
    assert len(TokenType) == 3, "Please update implementation after adding new TokenType!"

    # Current line index.
    current_line_index = 0

    # Get lines count.
    lines_count = len(lines)

    while current_line_index < lines_count:
        # Loop over lines.

        # Get line.
        current_line = lines[current_line_index]

        # Find first non space char.
        current_collumn_index = lexer_find_collumn(current_line, 0, lambda char: not char.isspace())

        # Get current line length.
        current_line_length = len(current_line)

        while current_collumn_index < current_line_length:
            # Iterate over line.

            # Get the location.
            current_location = (file_parent, current_line_index + 1, current_collumn_index + 1)

            if True:
                # Index of the column end.
                current_collumn_end_index = lexer_find_collumn(current_line, current_collumn_index,
                                                               lambda char: char.isspace())

                # Get current token text.
                current_token_text = current_line[current_collumn_index: current_collumn_end_index]

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
                            value=KEYWORD_NAMES_TO_TYPE[current_token_text]
                        )
                    else:
                        # Not keyword.

                        # If this is comment - break.
                        if current_token_text.startswith("//"):
                            break

                        # Return word token.
                        yield Token(
                            type=TokenType.WORD,
                            text=current_token_text,
                            location=current_location,
                            value=current_token_text
                        )
                else:
                    # If all ok.

                    # Return token.
                    yield Token(
                        type=TokenType.INTEGER,
                        text=current_token_text,
                        location=current_location,
                        value=current_token_integer
                    )

                # Find first non space char.
                current_collumn_index = lexer_find_collumn(current_line, current_collumn_end_index,
                                                           lambda char: not char.isspace())

        # Index of the column end.
        current_collumn_end_index = 0

        # Increment current line.
        current_line_index += 1


# Parser.

def parser_parse(tokens: List[Token], context: ParserContext):
    """ Parses token from lexer* (lexer_tokenize()) """

    # Check that there is no changes in operator type.
    assert len(OperatorType) == 4, "Please update implementation after adding new OperatorType!"

    # Check that there is no changes in keyword type.
    assert len(Keyword) == 2, "Please update implementation after adding new Keyword!"

    # Check that there is no changes in token type.
    assert len(TokenType) == 3, "Please update implementation after adding new TokenType!"

    # Reverse tokens.
    reversed_tokens: List[Token] = list(reversed(tokens))

    while len(reversed_tokens) > 0:
        # While there is any token.

        # Get current token.
        current_token = reversed_tokens.pop()

        if current_token.type == TokenType.WORD:
            # If we got a word.

            # Type check.
            assert isinstance(current_token.value, str), "Type error, lexer level error?"

            if current_token.value in INTRINSIC_NAMES_TO_TYPE:
                # If this is intrinsic.

                # Create operator.
                operator = Operator(
                    type=OperatorType.INTRINSIC,
                    token=current_token,
                    operand=INTRINSIC_NAMES_TO_TYPE[current_token.value]
                )

                # Add operator to the context.
                context.operators.append(operator)

                # Increment operator index.
                context.operator_index += 1
        elif current_token.type == TokenType.INTEGER:
            # If we got a integer.

            # Type check.
            assert isinstance(current_token.value, int), "Type error, lexer level error?"

            # Create operator.
            operator = Operator(
                type=OperatorType.PUSH_INTEGER,
                token=current_token,
                operand=current_token.value
            )

            # Add operator to the context.
            context.operators.append(operator)

            # Increment operator index.
            context.operator_index += 1
        elif current_token.type == TokenType.KEYWORD:
            # If we got a keyword.

            if current_token.value == Keyword.IF:
                # This is IF keyword.

                # Create operator.
                operator = Operator(
                    type=OperatorType.IF,
                    token=current_token
                )

                # Push operator to the context.
                context.operators.append(operator)

                # Push current operator index to the context memory stack.
                context.memory_stack.append(context.operator_index)

                # Increment operator index.
                context.operator_index += 1
            elif current_token.value == Keyword.ENDIF:
                # If this is endif keyword.

                # Get block operator index from the stack.
                block_operator_index = context.memory_stack.pop()

                if context.operators[block_operator_index].type == OperatorType.IF:
                    # If this is IF block.

                    # Create operator.
                    operator = Operator(
                        type=OperatorType.ENDIF,
                        token=current_token
                    )

                    # Push operator to the context.
                    context.operators.append(operator)

                    # Say that start IF block refers to this ENDIF block.
                    context.operators[block_operator_index].operand = context.operator_index

                    # Say that this ENDIF block refers to next operator index.
                    context.operators[context.operator_index].operand = context.operator_index + 1
                else:
                    # If invalid we call endif not after the if.

                    # Get error location.
                    error_location = context.operators[context.memory_stack.pop()].token.location

                    # Error message.
                    error_message(error_location, "Error", "`endif` can only close `if` block!")

                    # Exit at the parsing.
                    exit()

                # Increment operator index.
                context.operator_index += 1

            else:
                # If unknown keyword type.
                assert False, "Unknown keyword type! (How?)"
        else:
            # If unknown operator type.
            assert False, "Unknown operator type! (How?)"

    if len(context.memory_stack) > 0:
        # If there is any in the stack.

        # Get error location.
        error_location = context.operators[context.memory_stack.pop()].token.location

        # Error message.
        error_message(error_location, "Error", "Unclosed block!")

        # Exit at the parsing.
        exit()


# Interpretator.

def interpretator_run(source: Source):
    """ Interpretates the source. """

    # Create empty stack.
    memory_execution_stack: List[OPERAND] = []

    # Get source operators count.
    operators_count = len(source.operators)

    # Current operator index from the source.
    current_operator_index = 0

    # Check that there is no new operator type.
    assert len(OperatorType) == 4, "Please update implementation after adding new OperatorType!"

    # Check that there is no new instrinsic type.
    assert len(Intrinsic) == 8, "Please update implementation after adding new Intrinsic!"

    while current_operator_index < operators_count:
        # While we not run out of the source operators list.

        # Get current operator from the source.
        current_operator = source.operators[current_operator_index]

        # Grab our operator
        if current_operator.type == OperatorType.PUSH_INTEGER:
            # Push integer operator.

            # Type check.
            assert isinstance(current_operator.operand, int), "Type error, lexer level error?"

            # Push operand to the stack.
            memory_execution_stack.append(current_operator.operand)

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
                memory_execution_stack.append(operand_a + operand_b)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.MINUS:
                # Intristic minus operator.

                # Get both operands.
                operand_a = memory_execution_stack.pop()
                operand_b = memory_execution_stack.pop()

                # Push difference to the stack.
                memory_execution_stack.append(operand_b - operand_a)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.MULTIPLY:
                # Intristic multiply operator.

                # Get both operands.
                operand_a = memory_execution_stack.pop()
                operand_b = memory_execution_stack.pop()

                # Push muliply to the stack.
                memory_execution_stack.append(operand_a * operand_b)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.EQUAL:
                # Intristic equal operator.

                # Get both operands.
                operand_a = memory_execution_stack.pop()
                operand_b = memory_execution_stack.pop()

                # Push equal to the stack.
                memory_execution_stack.append(int(operand_a == operand_b))

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.NOT_EQUAL:
                # Intristic not equal operator.

                # Get both operands.
                operand_a = memory_execution_stack.pop()
                operand_b = memory_execution_stack.pop()

                # Push not equal to the stack.
                memory_execution_stack.append(int(operand_a != operand_b))

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.COPY:
                # Intristic copy operator.

                # Get operand.
                operand_a = memory_execution_stack.pop()

                # Push copy to the stack.
                memory_execution_stack.append(operand_a)
                memory_execution_stack.append(operand_a)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.FREE:
                # Intristic free operator.

                # Pop and left.
                memory_execution_stack.pop()

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.SHOW:
                # Intristic show operator.

                # Get operand.
                operand_a = memory_execution_stack.pop()

                # Show operand.
                print(operand_a)

                # Increase operator index.
                current_operator_index += 1
            else:
                # If unknown instrinsic type.
                assert False, "Unknown instrinsic! (How?)"
        elif current_operator.type == OperatorType.IF:
            # IF operator.

            # Get operand.
            operand_a = memory_execution_stack.pop()

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

            if operand_a == 0:
                # If this is false.

                # Jump to the operator operand.
                # As this is IF, so we should jump to the ENDIF.
                current_operator_index = current_operator.operand
            else:
                # If this is true.

                # Increment operator index.
                # This is makes jump into the if branch.
                current_operator_index += 1
        elif current_operator.type == OperatorType.ENDIF:
            # ENDIF operator.

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

            # Jump to the operator operand.
            # As this is ENDIF operator, we should have index + 1, index!
            current_operator_index = current_operator.operand
        else:
            # If unknown operator type.
            assert False, "Unknown operator type! (How?)"

    if len(memory_execution_stack) != 0:
        # If there is any in the stack.

        # Should be not called? (as we call type checker type_checker_static_type_check).

        # Error message.
        error_message(("__runner__", 1, 1), "Warning", "Stack is not empty after running the interpretation!")


# Linter.

def linter_type_check(source: Source, path: str):
    """ Linter static type check. """

    # Get the basename path.
    path = basename(path)

    # Create empty stack.
    memory_linter_stack: List[OPERAND] = []

    # Get source operators count.
    operators_count = len(source.operators)

    # Current operator index from the source.
    current_operator_index = 0

    # Check that there is no new operator type.
    assert len(OperatorType) == 4, "Please update implementation after adding new OperatorType!"

    # Check that there is no new instrinsic type.
    assert len(Intrinsic) == 8, "Please update implementation after adding new Intrinsic!"

    while current_operator_index < operators_count:
        # While we not run out of the source operators list.

        # Get current operator from the source.
        current_operator = source.operators[current_operator_index]

        # Grab our operator
        if current_operator.type == OperatorType.PUSH_INTEGER:
            # Push integer operator.

            # Type check.
            assert isinstance(current_operator.operand, int), "Type error, lexer level error?"

            # Push operand to the stack.
            memory_linter_stack.append(current_operator.operand)

            # Increase operator index.
            current_operator_index += 1
        elif current_operator.type == OperatorType.INTRINSIC:
            # Intrinsic operator.

            if current_operator.operand == Intrinsic.PLUS:
                # Intristic plus operator.

                # Check stack size.
                if len(memory_linter_stack) < 2:
                    no_arguments_error_message(current_operator)
                    exit()

                # Get both operands.
                operand_a = memory_linter_stack.pop()
                operand_b = memory_linter_stack.pop()

                # Push sum to the stack.
                memory_linter_stack.append(operand_a + operand_b)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.MINUS:
                # Intristic minus operator.

                # Check stack size.
                if len(memory_linter_stack) < 2:
                    no_arguments_error_message(current_operator)
                    exit()

                # Get both operands.
                operand_a = memory_linter_stack.pop()
                operand_b = memory_linter_stack.pop()

                # Push difference to the stack.
                memory_linter_stack.append(operand_b - operand_a)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.MULTIPLY:
                # Intristic multiply operator.

                # Check stack size.
                if len(memory_linter_stack) < 2:
                    no_arguments_error_message(current_operator)
                    exit()

                # Get both operands.
                operand_a = memory_linter_stack.pop()
                operand_b = memory_linter_stack.pop()

                # Push muliply to the stack.
                memory_linter_stack.append(operand_a * operand_b)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.EQUAL:
                # Intristic equal operator.

                # Check stack size.
                if len(memory_linter_stack) < 2:
                    no_arguments_error_message(current_operator)
                    exit()

                # Get both operands.
                operand_a = memory_linter_stack.pop()
                operand_b = memory_linter_stack.pop()

                # Push equal to the stack.
                memory_linter_stack.append(int(operand_a == operand_b))

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.NOT_EQUAL:
                # Intristic not equal operator.

                # Check stack size.
                if len(memory_linter_stack) < 2:
                    no_arguments_error_message(current_operator)
                    exit()

                # Get both operands.
                operand_a = memory_linter_stack.pop()
                operand_b = memory_linter_stack.pop()

                # Push not equal to the stack.
                memory_linter_stack.append(int(operand_a != operand_b))

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.COPY:
                # Intristic copy operator.

                # Check stack size.
                if len(memory_linter_stack) < 1:
                    no_arguments_error_message(current_operator)
                    exit()

                # Get operand.
                operand_a = memory_linter_stack.pop()

                # Push copy to the stack.
                memory_linter_stack.append(operand_a)
                memory_linter_stack.append(operand_a)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.FREE:
                # Intristic free operator.

                # Check stack size.
                if len(memory_linter_stack) < 1:
                    no_arguments_error_message(current_operator)
                    exit()

                # Pop and left.
                memory_linter_stack.pop()

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.SHOW:
                # Intristic show operator.

                # Check stack size.
                if len(memory_linter_stack) < 1:
                    no_arguments_error_message(current_operator)
                    exit()

                # Pop and left.
                memory_linter_stack.pop()

                # Increase operator index.
                current_operator_index += 1
            else:
                # If unknown instrinsic type.
                assert False, "Unknown instrinsic! (How?)"
        elif current_operator.type == OperatorType.IF:
            # IF operator.

            # Check stack size.
            if len(memory_linter_stack) < 1:
                no_arguments_error_message(current_operator)
                exit()

            # Get operand.
            operand_a = memory_linter_stack.pop()

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

            if operand_a == 0:
                # If this is false.

                # Jump to the operator operand.
                # As this is IF, so we should jump to the ENDIF.
                current_operator_index = current_operator.operand
            else:
                # If this is true.

                # Increment operator index.
                # This is makes jump into the if branch.
                current_operator_index += 1
        elif current_operator.type == OperatorType.ENDIF:
            # ENDIF operator.

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

            # Jump to the operator operand.
            # As this is ENDIF operator, we should have index + 1, index!
            current_operator_index = current_operator.operand
        else:
            # If unknown operator type.
            assert False, "Unknown operator type! (How?)"

    if len(memory_linter_stack) != 0:
        # If there is any in the stack.

        # Error message.
        error_message((path, current_operator_index, -1), "Warning", "Stack is not empty at the type checking stage!")


# Graph.

def graph_generate(source: Source, path: str):
    """ Generates graph from the source. """

    # Open file.
    file = open(path + ".dot", "w")

    # Get source operators count.
    operators_count = len(source.operators)

    # Current operator index from the source.
    current_operator_index = 0

    # Check that there is no changes in operator type.
    assert len(OperatorType) == 4, "Please update implementation after adding new OperatorType!"

    # Write header.
    file.write("digraph Source{\n")

    while current_operator_index < operators_count:
        # While we not run out of the source operators list.

        # Get current operator from the source.
        current_operator = source.operators[current_operator_index]

        # Grab our operator
        if current_operator.type == OperatorType.PUSH_INTEGER:
            # Push integer operator.

            # Type check.
            assert isinstance(current_operator.operand, int), "Type error, parser level error?"

            # Write node data.
            file.write(f"   Operator_{current_operator_index} [label=PUSH_{current_operator.operand}];\n")
            file.write(f"   Operator_{current_operator_index} -> Operator_{current_operator_index + 1};\n")
        elif current_operator.type == OperatorType.INTRINSIC:
            # Intrinsic operator.

            # Type check.
            assert isinstance(current_operator.operand, Intrinsic), f"Type error, parser level error?"

            # Write node data.
            file.write(f"   Operator_{current_operator_index} [label={repr(repr(INTRINSIC_TYPES_TO_NAME[current_operator.operand]))}];\n")
            file.write(f"   Operator_{current_operator_index} -> Operator_{current_operator_index + 1};\n")
        elif current_operator.type == OperatorType.IF:
            # If operator.

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), f"Type error, parser level error?"

            # Write node data.
            file.write(f"   Operator_{current_operator_index} [shape=record label=if];\n")
            file.write(f"   Operator_{current_operator_index} -> Operator_{current_operator_index + 1} [label=true];\n")
            file.write(f"   Operator_{current_operator_index} -> Operator_{current_operator.operand} [label=false];\n")
        elif current_operator.type == OperatorType.ENDIF:
            # Endif operator.

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

            # Write node data.
            file.write(f"   Operator_{current_operator_index} [shape=record label=endif];\n")
            file.write(f"   Operator_{current_operator_index} -> Operator_{current_operator.operand};\n")
        else:
            # If unknown operator type.
            assert False, f"Unknown operator type! (How?)"

        # Increment current index.
        current_operator_index += 1

    # Mark Last as the end.
    file.write(f"   Operator_{current_operator_index} [label=\"EndOfOperators\"];\n")

    # Write footer.
    file.write("}\n")

    # Close file.
    file.close()


# Python.

def python_generate(source: Source, path: str):
    """ Generates graph from the source. """

    # Open file.
    file = open(path + ".py", "w")

    # Get source operators count.
    operators_count = len(source.operators)

    # Current operator index from the source.
    current_operator_index = 0

    # Indentation level.
    current_indent_level = 0

    # Check that there is no changes in operator type or intrinsic.
    assert len(OperatorType) == 4, "Please update implementation after adding new OperatorType!"
    assert len(Intrinsic) == 8, "Please update implementation after adding new Intrinsic!"

    # Write header.
    file.write("# This file is auto-generated by MSPL python subcommand! \n")
    file.write("\n")
    file.write("# Allocate stack (As is MSPL is Stack-Oriented Language): \n")
    file.write("stack = list()\n")
    file.write("\n")
    file.write("# Work with stack functions: \n")
    file.write("def push(v):\n\tstack.append(v)\n")
    file.write("def pop():\n\treturn stack.pop()\n")
    file.write("\n\n")
    file.write(f"# Source ({basename(path)}): \n")

    while current_operator_index < operators_count:
        # While we not run out of the source operators list.

        # Get current operator from the source.
        current_operator = source.operators[current_operator_index]

        # Get comment data.
        location = "Line %d, Row %d" % current_operator.token.location[1:3]
        comment = f"Text: {current_operator.token.text} [{location}]"

        # Grab our operator
        if current_operator.type == OperatorType.PUSH_INTEGER:
            # Push integer operator.

            # Type check.
            assert isinstance(current_operator.operand, int), "Type error, parser level error?"

            # Write data.
            file.write("\t" * current_indent_level + f"push({current_operator.operand})  # {comment}\n\n")
        elif current_operator.type == OperatorType.INTRINSIC:
            # Intrinsic operator.

            # Type check.
            assert isinstance(current_operator.operand, Intrinsic), f"Type error, parser level error?"

            if current_operator.operand == Intrinsic.PLUS:
                # Intristic plus operator.

                # Write node data.
                file.write("\t" * current_indent_level + f"push(pop() + pop())  # {comment}\n\n")
            elif current_operator.operand == Intrinsic.MINUS:
                # Intristic minus operator.

                # Write node data.
                file.write("\t" * current_indent_level + f"push(pop() - pop())  # {comment}\n\n")
            elif current_operator.operand == Intrinsic.MULTIPLY:
                # Intristic multiply operator.

                # Write node data.
                file.write("\t" * current_indent_level + f"push(pop() * pop())  # {comment}\n\n")
            elif current_operator.operand == Intrinsic.EQUAL:
                # Intristic equal operator.

                # Write node data.
                file.write("\t" * current_indent_level + f"push(int(pop() == pop()))  # {comment}\n\n")
            elif current_operator.operand == Intrinsic.NOT_EQUAL:
                # Intristic not equal operator.

                # Write node data.
                file.write("\t" * current_indent_level + f"push(int(pop() != pop()))  # {comment}\n\n")
            elif current_operator.operand == Intrinsic.COPY:
                # Intristic copy operator.

                # Write node data.
                file.write("\t" * current_indent_level + f"buffer = pop()  # {comment}\n")
                file.write("\t" * current_indent_level + f"push(buffer)  # {comment}\n")
                file.write("\t" * current_indent_level + f"push(buffer)  # {comment}\n\n")
            elif current_operator.operand == Intrinsic.SHOW:
                # Intristic show operator.

                # Write node data.
                file.write("\t" * current_indent_level + f"print(pop())  # {comment}\n")
            elif current_operator.operand == Intrinsic.FREE:
                # Intristic free operator.

                # Write node data.
                file.write("\t" * current_indent_level + f"pop()  # {comment}\n")
            else:
                # If unknown instrinsic type.

                # Write node data.
                file.write("\t" * current_indent_level + f"# Sorry, but this intrinsic is not implemented yet! {comment}\n\n")
        elif current_operator.type == OperatorType.IF:
            # If operator.

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), f"Type error, parser level error?"

            # Write node data.
            file.write("\t" * current_indent_level + f"if pop() != 0:  # {comment}\n")

            # Increase indent level.
            current_indent_level += 1
        elif current_operator.type == OperatorType.ENDIF:
            # Endif operator.

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

            # Decrease indent level.
            current_indent_level -= 1
        else:
            # If unknown operator type.
            assert False, f"Unknown operator type! (How?)"

        # Increment current index.
        current_operator_index += 1

    # Close file.
    file.close()


if __name__ == "__main__":
    # Entry point.

    # CLI Options.
    cli_source_path = f"{getcwd()}\\" + "examples\\if_example.mspl"
    cli_subcommand = "interpretate"
    cli_supress_linter = False

    if cli_subcommand == "interpretate":
        # If this is interpretate subcommand.

        # Message.
        print(f"[Info] Running source file \"{basename(cli_source_path)}\"")

        # Read source lines.
        with open(cli_source_path, "r", encoding="UTF-8") as source_file:
            source_lines = source_file.readlines()

        # Parser context.
        parser_context = ParserContext()

        # Tokenize.
        lexer_tokens = list(lexer_tokenize(source_lines, cli_source_path))

        # Parse.
        parser_parse(lexer_tokens, parser_context)

        # Create source from context.
        parser_context_source = Source(parser_context.operators)

        # Type check.
        if not cli_supress_linter:
            linter_type_check(parser_context_source, cli_source_path)

        # Run interpretation.
        interpretator_run(parser_context_source)

        # Message.
        print(f"[Info] File \"{basename(cli_source_path)}\" was run!")
    elif cli_subcommand == "graph":
        # If this is graph subcommand.

        # Message.
        print(f"[Info] Generating .dot file for source file \"{basename(cli_source_path)}\"")

        # Read source lines.
        with open(cli_source_path, "r", encoding="UTF-8") as source_file:
            source_lines = source_file.readlines()

        # Parser context.
        parser_context = ParserContext()

        # Tokenize.
        lexer_tokens = list(lexer_tokenize(source_lines, cli_source_path))

        # Parse.
        parser_parse(lexer_tokens, parser_context)

        # Create source from context.
        parser_context_source = Source(parser_context.operators)

        # Type check.
        if not cli_supress_linter:
            linter_type_check(parser_context_source, cli_source_path)

        # Generate graph file.
        graph_generate(parser_context_source, cli_source_path)

        # Message.
        print(f"[Info] .dot file \"{basename(cli_source_path)}.dot\" generated!")
    elif cli_subcommand == "python":
        # If this is python subcommand.

        # Message.
        print(f"[Info] Generating .py file for source file \"{basename(cli_source_path)}\"")

        # Read source lines.
        with open(cli_source_path, "r", encoding="UTF-8") as source_file:
            source_lines = source_file.readlines()

        # Parser context.
        parser_context = ParserContext()

        # Tokenize.
        lexer_tokens = list(lexer_tokenize(source_lines, cli_source_path))

        # Parse.
        parser_parse(lexer_tokens, parser_context)

        # Create source from context.
        parser_context_source = Source(parser_context.operators)

        # Type check.
        if not cli_supress_linter:
            linter_type_check(parser_context_source, cli_source_path)

        # Generate python file.
        python_generate(parser_context_source, cli_source_path)

        # Message.
        print(f"[Info] .py file \"{basename(cli_source_path)}.py\" generated!")
    else:
        # If unknown subcommand.

        # Message.
        print("[Error] Sorry, you entered unknown subcommand!")

