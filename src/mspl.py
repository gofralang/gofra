# MSPL Source Code.
# "Most Simple|Stupid Programming Language".

# Dataclass.
from dataclasses import dataclass, field

# System error.
from sys import stderr, stdout

# Current working directory and basename.
from os.path import basename

# Enum for types.
from enum import IntEnum, Enum, auto

# Typing for type hints.
from typing import Optional, Union, Tuple, List, Dict, Callable, Generator

# CLI.
from sys import argv


class Stack:
    """ Stack implementation for the language (More optional then useful). """

    # Empty list as stack.
    __stack = list()

    def push(self, value):
        """ Push any value on the stack. """

        # Push.
        self.__stack.append(value)

    def pop(self):
        """ Pop any value from the stack. """

        # Pop.
        return self.__stack.pop()

    def __len__(self):
        """ Magic __len__(). """

        # Check length.
        return len(self.__stack)


class Stage(Enum):
    """ Enumeration for stage types. """
    LEXER = auto(),
    PARSER = auto(),
    LINTER = auto()
    RUNNER = auto()
    COMPILATOR = auto()


class DataType(IntEnum):
    """ Enumeration for datatype types. """
    INTEGER = auto()


class Keyword(Enum):
    """ Enumeration for keyword types. """

    # Conditions.
    IF = auto()
    ELSE = auto()
    ENDIF = auto()


class Intrinsic(Enum):
    """ Enumeration for intrinsic types. """

    # Int.
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()

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
    ELSE = auto()
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
assert len(Intrinsic) == 9, "Please update INTRINSIC_NAMES_TO_TYPE after adding new Intrinsic!"
INTRINSIC_NAMES_TO_TYPE: Dict[str, Intrinsic] = {
    "+": Intrinsic.PLUS,
    "-": Intrinsic.MINUS,
    "*": Intrinsic.MULTIPLY,
    "/": Intrinsic.DIVIDE,
    "==": Intrinsic.EQUAL,
    "!=": Intrinsic.NOT_EQUAL,
    "show": Intrinsic.SHOW,
    "copy": Intrinsic.COPY,
    "free": Intrinsic.FREE
}
INTRINSIC_TYPES_TO_NAME: Dict[Intrinsic, str] = {
    value: key for key, value in INTRINSIC_NAMES_TO_TYPE.items()
}

# Stage names.
assert len(Stage) == 5, "Please update STAGE_TYPES_TO_NAME after adding new Stage!"
STAGE_TYPES_TO_NAME: Dict[Stage, str] = {
    Stage.LEXER: "Lexing",
    Stage.PARSER: "Parsing",
    Stage.LINTER: "Linter",
    Stage.RUNNER: "Running",
    Stage.COMPILATOR: "Compilation"
}

# Keyword names / types.
assert len(Keyword) == 3, "Please update KEYWORD_NAMES_TO_TYPE after adding new Keyword!"
KEYWORD_NAMES_TO_TYPE: Dict[str, Keyword] = {
    "if": Keyword.IF,
    "else": Keyword.ELSE,
    "endif": Keyword.ENDIF,
}

# Extra `tokens`.
EXTRA_COMMENT = "//"
EXTRA_DIRECTIVE = "#"


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

    # Directives.
    directive_linter_skip: bool = False
    directive_python_comments_skip: bool = False


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
                        # TODO: Try to fix something like 0//0 (comment not at the start) will lex not as should.
                        if current_token_text.startswith(EXTRA_COMMENT):
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

        # Increment current line.
        current_line_index += 1


# Parser.

def parser_parse(tokens: List[Token], context: ParserContext, path: str):
    """ Parses token from lexer* (lexer_tokenize()) """

    # Check that there is no changes in operator type.
    assert len(OperatorType) == 5, "Please update implementation after adding new OperatorType!"

    # Check that there is no changes in keyword type.
    assert len(Keyword) == 3, "Please update implementation after adding new Keyword!"

    # Check that there is no changes in token type.
    assert len(TokenType) == 3, "Please update implementation after adding new TokenType!"

    # Reverse tokens.
    reversed_tokens: List[Token] = list(reversed(tokens))

    if len(reversed_tokens) == 0:
        # If there is no tokens.

        # Error.
        cli_error_message_verbosed(Stage.PARSER, (basename(path), 1, 1), "Error",
                                   "There is no tokens found, are you given empty file?", True)

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
            else:
                # If not intrinsic.

                if current_token.text.startswith(EXTRA_DIRECTIVE):
                    # If this is directive.

                    # Grab the directive.
                    directive = current_token.text[len(EXTRA_DIRECTIVE):]

                    if directive == "LINTER_SKIP":
                        # If this linter skip directive.

                        if context.directive_linter_skip:
                            # If already enabled.

                            # Message.
                            cli_error_message_verbosed(Stage.PARSER, current_token.location, "Error",
                                                       f"Directive `{EXTRA_DIRECTIVE}{directive}` defined twice!", True)

                        # Skip linter.
                        context.directive_linter_skip = True
                    elif directive == "PYTHON_COMMENTS_SKIP":
                        # If this python skip comments directive.

                        if context.directive_python_comments_skip:
                            # If already enabled.

                            # Message.
                            cli_error_message_verbosed(Stage.PARSER, current_token.location, "Error",
                                                       f"Directive `{EXTRA_DIRECTIVE}{directive}` defined twice!", True)

                        # Skip comments.
                        context.directive_python_comments_skip = True
                    else:
                        # If this is unknown direcitve.

                        # Message.
                        cli_error_message_verbosed(Stage.PARSER, current_token.location, "Error",
                                                   f"Unknown directive `{EXTRA_DIRECTIVE}{directive}`", True)
                else:
                    # Message.
                    cli_error_message_verbosed(Stage.PARSER, current_token.location, "Error",
                                               f"Unknown WORD `{current_token.text}`, are you misspelled something?",
                                               True)
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
            elif current_token.value == Keyword.ELSE:
                # If this is else keyword.

                if len(context.memory_stack) == 0:
                    # If there is nothing on the memory stack.

                    # Error.
                    cli_error_message_verbosed(Stage.PARSER,  current_token.location, "Error",
                                               "`else` should used after the `if` block!", True)

                # Get `IF` operator from the memory stack.
                block_operator_index = context.memory_stack.pop()
                block_operator = context.operators[block_operator_index]

                if block_operator.type == OperatorType.IF:
                    # If we use else after the IF.

                    # Say that previous IF should jump at the our+1 operator index.
                    context.operators[block_operator_index].operand = context.operator_index + 1

                    # Push current operator index to the stack.
                    context.memory_stack.append(context.operator_index)

                    # Create operator.
                    operator = Operator(
                        type=OperatorType.ELSE,
                        token=current_token
                    )

                    # Push operator to the context.
                    context.operators.append(operator)

                    # Increment operator index.
                    context.operator_index += 1
                else:
                    # Error message.
                    cli_error_message_verbosed(Stage.PARSER, error_location, "Error",
                                               "`else` can only used after `if` block!", True)

            elif current_token.value == Keyword.ENDIF:
                # If this is endif keyword.

                # Get block operator from the stack.
                block_operator_index = context.memory_stack.pop()
                block_operator = context.operators[block_operator_index]

                if block_operator.type == OperatorType.IF:
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
                if block_operator.type == OperatorType.ELSE:
                    # If this is ELSE block.

                    # Create operator.
                    operator = Operator(
                        type=OperatorType.ENDIF,
                        token=current_token
                    )

                    # Push operator to the context.
                    context.operators.append(operator)

                    # Say that owner block (If/Else) should jump to us.
                    context.operators[block_operator_index].operand = context.operator_index

                    # Say that we should jump to the next position.
                    context.operators[context.operator_index].operand = context.operator_index + 1
                else:
                    # If invalid we call endif not after the if.

                    # Get error location.
                    error_location = context.operators[context.memory_stack.pop()].token.location

                    # Error message.
                    cli_error_message_verbosed(Stage.PARSER, error_location, "Error",
                                               "`endif` can only close `if` block!", True)

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
        cli_error_message_verbosed(Stage.PARSER, error_location, "Error", "Unclosed block!", True)

    if context.directive_linter_skip:
        # If skip linter.

        # Error message.
        cli_error_message_verbosed(Stage.PARSER, (basename(path), 1, 1), "Warning",
                                   "LINTER SKIP DIRECTIVE! THIS IS UNSAFE!")


# Interpretator.

def interpretator_run(source: Source):
    """ Interpretates the source. """

    # Create empty stack.
    memory_execution_stack: Stack = Stack()

    # Get source operators count.
    operators_count = len(source.operators)

    # Current operator index from the source.
    current_operator_index = 0

    # Check that there is no new operator type.
    assert len(OperatorType) == 5, "Please update implementation after adding new OperatorType!"

    # Check that there is no new instrinsic type.
    assert len(Intrinsic) == 9, "Please update implementation after adding new Intrinsic!"

    while current_operator_index < operators_count:
        # While we not run out of the source operators list.

        # Get current operator from the source.
        current_operator = source.operators[current_operator_index]

        try:
            # Try / Catch to get unexpected Python errors.

            if current_operator.type == OperatorType.PUSH_INTEGER:
                # Push integer operator.

                # Type check.
                assert isinstance(current_operator.operand, int), "Type error, lexer level error?"

                # Push operand to the stack.
                memory_execution_stack.push(current_operator.operand)

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
                    memory_execution_stack.push(operand_a + operand_b)

                    # Increase operator index.
                    current_operator_index += 1
                elif current_operator.operand == Intrinsic.DIVIDE:
                    # Intristic divide operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push divide to the stack.
                    memory_execution_stack.push(operand_a % operand_b)

                    # Increase operator index.
                    current_operator_index += 1
                elif current_operator.operand == Intrinsic.MINUS:
                    # Intristic minus operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push difference to the stack.
                    memory_execution_stack.push(operand_b - operand_a)

                    # Increase operator index.
                    current_operator_index += 1
                elif current_operator.operand == Intrinsic.MULTIPLY:
                    # Intristic multiply operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push muliply to the stack.
                    memory_execution_stack.push(operand_a * operand_b)

                    # Increase operator index.
                    current_operator_index += 1
                elif current_operator.operand == Intrinsic.EQUAL:
                    # Intristic equal operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push equal to the stack.
                    memory_execution_stack.push(int(operand_a == operand_b))

                    # Increase operator index.
                    current_operator_index += 1
                elif current_operator.operand == Intrinsic.NOT_EQUAL:
                    # Intristic not equal operator.

                    # Get both operands.
                    operand_a = memory_execution_stack.pop()
                    operand_b = memory_execution_stack.pop()

                    # Push not equal to the stack.
                    memory_execution_stack.push(int(operand_a != operand_b))

                    # Increase operator index.
                    current_operator_index += 1
                elif current_operator.operand == Intrinsic.COPY:
                    # Intristic copy operator.

                    # Get operand.
                    operand_a = memory_execution_stack.pop()

                    # Push copy to the stack.
                    memory_execution_stack.push(operand_a)
                    memory_execution_stack.push(operand_a)

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
            elif current_operator.type == OperatorType.ELSE:
                # ELSE operator.

                # Type check.
                assert isinstance(current_operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

                # Jump to the operator operand.
                # As this is ELSE operator, we should have index + 1, index!
                current_operator_index = current_operator.operand
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
        except IndexError:
            # Stack* error.

            # Error message.
            cli_error_message_verbosed(Stage.RUNNER, current_operator.token.location, "Error",
                                       f"IndexError! This should be stack error (pop() when stack is empty?). "
                                       f"Do you used {EXTRA_DIRECTIVE}LINTER_SKIP directive? (From: "
                                       f"{current_operator.token.text})", True)

    if len(memory_execution_stack) > 0:
        # If there is any in the stack.

        # Should be not called? (as we call type checker type_checker_static_type_check).

        # Error message.
        cli_error_message_verbosed(Stage.RUNNER, ("__runner__", 1, 1), "Warning",
                                   "Stack is not empty after running the interpretation!")


# Linter.

def linter_type_check(source: Source):
    """ Linter static type check. """

    # Create empty stack.
    memory_linter_stack = Stack()

    # Get source operators count.
    operators_count = len(source.operators)

    # Current operator index from the source.
    current_operator_index = 0

    # Check that there is no new operator type.
    assert len(OperatorType) == 5, "Please update implementation after adding new OperatorType!"

    # Check that there is no new instrinsic type.
    assert len(Intrinsic) == 9, "Please update implementation after adding new Intrinsic!"

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
            memory_linter_stack.push(current_operator.operand)

            # Increase operator index.
            current_operator_index += 1
        elif current_operator.type == OperatorType.INTRINSIC:
            # Intrinsic operator.

            if current_operator.operand == Intrinsic.PLUS:
                # Intristic plus operator.

                # Check stack size.
                if len(memory_linter_stack) < 2:
                    cli_no_arguments_error_message(current_operator, True)

                # Get both operands.
                operand_a = memory_linter_stack.pop()
                operand_b = memory_linter_stack.pop()

                # Push sum to the stack.
                memory_linter_stack.push(operand_a + operand_b)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.DIVIDE:
                # Intristic divide operator.

                # Check stack size.
                if len(memory_linter_stack) < 2:
                    cli_no_arguments_error_message(current_operator, True)

                # Get both operands.
                operand_a = memory_linter_stack.pop()
                operand_b = memory_linter_stack.pop()

                # Push divide to the stack.
                memory_linter_stack.push(operand_a % operand_b)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.MINUS:
                # Intristic minus operator.

                # Check stack size.
                if len(memory_linter_stack) < 2:
                    cli_no_arguments_error_message(current_operator, True)

                # Get both operands.
                operand_a = memory_linter_stack.pop()
                operand_b = memory_linter_stack.pop()

                # Push difference to the stack.
                memory_linter_stack.push(operand_b - operand_a)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.MULTIPLY:
                # Intristic multiply operator.

                # Check stack size.
                if len(memory_linter_stack) < 2:
                    cli_no_arguments_error_message(current_operator, True)

                # Get both operands.
                operand_a = memory_linter_stack.pop()
                operand_b = memory_linter_stack.pop()

                # Push muliply to the stack.
                memory_linter_stack.push(operand_a * operand_b)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.EQUAL:
                # Intristic equal operator.

                # Check stack size.
                if len(memory_linter_stack) < 2:
                    cli_no_arguments_error_message(current_operator, True)

                # Get both operands.
                operand_a = memory_linter_stack.pop()
                operand_b = memory_linter_stack.pop()

                # Push equal to the stack.
                memory_linter_stack.push(int(operand_a == operand_b))

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.NOT_EQUAL:
                # Intristic not equal operator.

                # Check stack size.
                if len(memory_linter_stack) < 2:
                    cli_no_arguments_error_message(current_operator, True)

                # Get both operands.
                operand_a = memory_linter_stack.pop()
                operand_b = memory_linter_stack.pop()

                # Push not equal to the stack.
                memory_linter_stack.push(int(operand_a != operand_b))

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.COPY:
                # Intristic copy operator.

                # Check stack size.
                if len(memory_linter_stack) < 1:
                    cli_no_arguments_error_message(current_operator, True)

                # Get operand.
                operand_a = memory_linter_stack.pop()

                # Push copy to the stack.
                memory_linter_stack.push(operand_a)
                memory_linter_stack.push(operand_a)

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.FREE:
                # Intristic free operator.

                # Check stack size.
                if len(memory_linter_stack) < 1:
                    cli_no_arguments_error_message(current_operator, True)

                # Pop and left.
                memory_linter_stack.pop()

                # Increase operator index.
                current_operator_index += 1
            elif current_operator.operand == Intrinsic.SHOW:
                # Intristic show operator.

                # Check stack size.
                if len(memory_linter_stack) < 1:
                    cli_no_arguments_error_message(current_operator, True)

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
                cli_no_arguments_error_message(current_operator, True)

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
        elif current_operator.type == OperatorType.ELSE:
            # ELSE operator.

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

            # Jump to the operator operand.
            # As this is ELSE operator, we should have index + 1, index!
            current_operator_index = current_operator.operand
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

        # Get last operator location.
        location = source.operators[current_operator_index - 1].token.location

        # Error message.
        cli_error_message_verbosed(Stage.LINTER, location, "Error",
                                   f"Stack is not empty at the type checking stage! "
                                   f"(There is {len(memory_linter_stack)} elements when should be 0)", True)


# Source.


def load_source_from_file(file_path: str) -> \
        tuple[Union[Source, type(FileNotFoundError)], Union[ParserContext, type(FileNotFoundError)]]:
    """ Load file, then return ready source and context for it. (Tokenized, Parsed, Linted). """

    # Read source lines.
    try:
        with open(file_path, "r", encoding="UTF-8") as source_file:
            source_lines = source_file.readlines()
    except FileNotFoundError:
        # Return.
        return FileNotFoundError, FileNotFoundError

    # Parser context.
    parser_context = ParserContext()

    # Tokenize.
    lexer_tokens = list(lexer_tokenize(source_lines, file_path))

    # Parse.
    parser_parse(lexer_tokens, parser_context, file_path)

    # Create source from context.
    parser_context_source = Source(parser_context.operators)

    # Type check.
    if not parser_context.directive_linter_skip:
        linter_type_check(parser_context_source)

    # Return source and parser context.
    return parser_context_source, parser_context


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
    assert len(OperatorType) == 5, "Please update implementation after adding new OperatorType!"

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
            label = repr(repr(INTRINSIC_TYPES_TO_NAME[current_operator.operand]))
            file.write(f"   Operator_{current_operator_index} [label={label}];\n")
            file.write(f"   Operator_{current_operator_index} -> Operator_{current_operator_index + 1};\n")
        elif current_operator.type == OperatorType.IF:
            # If operator.

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), f"Type error, parser level error?"

            # Write node data.
            file.write(f"   Operator_{current_operator_index} [shape=record label=if];\n")
            file.write(f"   Operator_{current_operator_index} -> Operator_{current_operator_index + 1} [label=true];\n")
            file.write(f"   Operator_{current_operator_index} -> Operator_{current_operator.operand} [label=false];\n")
        elif current_operator.type == OperatorType.ELSE:
            # Else operator.

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

            # Write node data.
            file.write(f"   Operator_{current_operator_index} [shape=record label=else];\n")
            file.write(f"   Operator_{current_operator_index} -> Operator_{current_operator.operand};\n")
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

def python_generate(source: Source, context: ParserContext, path: str):
    """ Generates graph from the source. """

    # Open file.
    file = open(path + ".py", "w")

    # Should we skip comments.
    directive_skip_comments = context.directive_python_comments_skip

    # Get source operators count.
    operators_count = len(source.operators)

    # Current operator index from the source.
    current_operator_index = 0

    # Indentation level.
    current_indent_level = 0
    current_indent = ""

    # Check that there is no changes in operator type or intrinsic.
    assert len(OperatorType) == 5, "Please update implementation after adding new OperatorType!"
    assert len(Intrinsic) == 9, "Please update implementation after adding new Intrinsic!"

    # Write header.
    if not directive_skip_comments:
        file.write("# This file is auto-generated by MSPL python subcommand! \n")
        file.write("\n")
        file.write("# Allocate stack (As is MSPL is Stack-Based Language): \n")
    file.write("stack = list()\n")
    if not directive_skip_comments:
        file.write("\n")
        file.write("# Work with stack functions: \n")
    file.write("def push(v):\n\tstack.append(v)\n")
    file.write("def pop():\n\treturn stack.pop()\n")
    if not directive_skip_comments:
        file.write("\n\n")
        file.write(f"# Source ({basename(path)}): \n")

    while current_operator_index < operators_count:
        # While we not run out of the source operators list.

        # Get current operator from the source.
        current_operator = source.operators[current_operator_index]

        # Get comment data.
        location = "Line %d, Row %d" % current_operator.token.location[1:3]
        comment = f"  # Token: {current_operator.token.text} [{location}]"
        if directive_skip_comments:
            comment = ""

        # Grab our operator
        if current_operator.type == OperatorType.PUSH_INTEGER:
            # Push integer operator.

            # Type check.
            assert isinstance(current_operator.operand, int), "Type error, parser level error?"

            # Write data.
            file.write(current_indent + f"push({current_operator.operand}){comment}\n")
        elif current_operator.type == OperatorType.INTRINSIC:
            # Intrinsic operator.

            # Type check.
            assert isinstance(current_operator.operand, Intrinsic), f"Type error, parser level error?"

            if current_operator.operand == Intrinsic.PLUS:
                # Intristic plus operator.

                # Write node data.
                file.write(current_indent + f"push(pop() + pop()){comment}\n")
            elif current_operator.operand == Intrinsic.MINUS:
                # Intristic minus operator.

                # Write node data.
                file.write(current_indent + f"push(pop() - pop()){comment}\n")
            elif current_operator.operand == Intrinsic.MULTIPLY:
                # Intristic multiply operator.

                # Write node data.
                file.write(current_indent + f"push(pop() * pop()){comment}\n")
            elif current_operator.operand == Intrinsic.DIVIDE:
                # Intristic divide operator.

                # Write node data.
                file.write(current_indent + f"push(pop() % pop()){comment}\n")
            elif current_operator.operand == Intrinsic.EQUAL:
                # Intristic equal operator.

                # Write node data.
                file.write(current_indent + f"push(int(pop() == pop())){comment}\n")
            elif current_operator.operand == Intrinsic.NOT_EQUAL:
                # Intristic not equal operator.

                # Write node data.
                file.write(current_indent + f"push(int(pop() != pop())){comment}\n")
            elif current_operator.operand == Intrinsic.COPY:
                # Intristic copy operator.

                # Write node data.
                file.write(current_indent + f"buffer = pop(){comment}\n")
                file.write(current_indent + f"push(buffer){comment}\n")
                file.write(current_indent + f"push(buffer){comment}\n")
            elif current_operator.operand == Intrinsic.SHOW:
                # Intristic show operator.

                # Write node data.
                file.write(current_indent + f"print(pop()){comment}\n")
            elif current_operator.operand == Intrinsic.FREE:
                # Intristic free operator.

                # Write node data.
                file.write(current_indent + f"pop(){comment}\n")
            else:
                # If unknown instrinsic type.

                # Write node data.
                cli_error_message_verbosed(Stage.COMPILATOR, current_operator.token.location, "Error",
                                           f"Intrinsic {INTRINSIC_TYPES_TO_NAME[current_operator.operand]} is not implemented for"
                                           f"python generation!", True)
        elif current_operator.type == OperatorType.IF:
            # If operator.

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), f"Type error, parser level error?"

            # Write node data.
            file.write(current_indent + f"if pop() != 0:{comment}\n")

            # Increase indent level.
            current_indent_level += 1
            current_indent = "\t" * current_indent_level
        elif current_operator.type == OperatorType.ELSE:
            # Else operator.

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

            # Decrease indent level.
            current_indent_level -= 1
            current_indent = "\t" * current_indent_level

            # Write node data.
            file.write(current_indent + f"else:{comment}\n")

            # Increase indent level.
            current_indent_level += 1
            current_indent = "\t" * current_indent_level
        elif current_operator.type == OperatorType.ENDIF:
            # Endif operator.

            # Type check.
            assert isinstance(current_operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

            # Decrease indent level.
            current_indent_level -= 1
            current_indent = "\t" * current_indent_level
        else:
            # If unknown operator type.
            assert False, f"Unknown operator type! (How?)"

        # Increment current index.
        current_operator_index += 1

    # Close file.
    file.close()


# CLI.


def cli_error_message_verbosed(stage: Stage, location: LOCATION, level: str, text: str, force_exit: bool = False):
    """ Shows verbosed error message to the CLI. """

    # Message.
    print(f"[{level} at `{STAGE_TYPES_TO_NAME[stage]}` stage] ({location[0]}) on {location[1]}:{location[2]} - {text}",
          file=stderr)

    # If we should force exit.
    if force_exit:
        exit(1)


def cli_error_message(level: str, text: str, force_exit: bool = False):
    """ Shows error message to the CLI. """

    # Message.
    print(f"[{level}] {text}", file=stderr)

    # If we should force exit.
    if force_exit:
        exit(1)


def cli_no_arguments_error_message(operator: Operator, force_exit: bool = False):
    """ Shows no arguments passed error message to the CLI. """

    if operator.type == OperatorType.INTRINSIC:
        # Intrinsic Operator.

        # Type check.
        assert isinstance(operator.operand, Intrinsic), "Type error, parser level error?"

        # Error
        cli_error_message_verbosed(Stage.LINTER, operator.token.location, "Error",
                                   f"`{INTRINSIC_TYPES_TO_NAME[operator.operand]}` "
                                   f"intrinsic should have more arguments at the stack, but it was not founded!")

    elif operator.type == OperatorType.IF:
        # IF Operator.

        # Error
        cli_error_message_verbosed(Stage.LINTER, operator.token.location, "Error",
                                   "`IF` operator should have 1 argument at the stack, but it was not found!")
    else:
        # Unknown operator.
        assert False, "Tried to call no_arguments_error_message() " \
                      "for operator that does not need arguments! (Type checker error?)"

    # If we should force exit.
    if force_exit:
        exit(1)


def cli_validate_argument_vector(argument_vector: List[str]) -> List[str]:
    """ Validates CLI argv (argument vector) """

    # Check that ther is any in the ARGV.
    assert len(argument_vector) > 0, "There is no source(mspl.py) file path in the ARGV"

    # Get argument vector without source(mspl.py) path.
    argument_runner_filename = argument_vector[0]
    argument_vector = argument_vector[1:]

    # Validate ARGV.
    if len(argument_vector) == 0:
        # If there is no arguments.

        # Message.
        cli_usage_message(argument_runner_filename)
        cli_error_message("Error", "Please pass file path to work with (.mspl extension)", True)
    elif len(argument_vector) == 1:
        # Just one argument.

        if argument_vector[0] != "help":
            # If this is not help.

            # Message.
            cli_usage_message(argument_runner_filename)
            cli_error_message("Error", "Please pass subcommand after the file path!", True)

        # Show usage.
        cli_usage_message(argument_runner_filename)

        # Exit.
        exit(0)

        # Return path as source file and help (argv[0]).
        return ["", argument_vector[0]]
    elif len(argument_vector) == 2:
        # Expected ARGV length.
        pass
    else:
        # Message.
        cli_usage_message(argument_runner_filename)
        cli_error_message("Error", "Unexpected arguments!", True)

    # Return final ARGV.
    return argument_vector


def cli_welcome_message():
    """ Shows CLI welcome message. """

    # Show.
    print(f"[MSPL CLI] Welcome there!", file=stdout)


def cli_usage_message(runner_filename: str = None):
    """ Shows CLI usage message. """

    # Set runner as __file__ if is not given.
    if runner_filename is None:
        runner_filename = __file__

    # Show.
    print(f"Usage: {basename(runner_filename)} [source] [subcommand]\nSubcommands:\n"
          f"\thelp; Show this message.\n"
          f"\trun; Intrerpretates source in Python.\n"
          f"\tpython; Generates python file from the source in output file [source*.mspl].py\n"
          f"\tgraph; Generates graphviz file from the source in output file [source*.mspl].dot", file=stdout)


def cli_entry_point():
    """ Entry point for the CLI. """

    # Welcome message.
    cli_welcome_message()

    # CLI Options.
    cli_source_path, cli_subcommand = cli_validate_argument_vector(argv)

    if cli_subcommand == "run":
        # If this is interpretate subcommand.

        # Get source.
        cli_source, _ = load_source_from_file(cli_source_path)

        # File exists check.
        if cli_source is FileNotFoundError:
            cli_error_message("Error", f"File \"{cli_source_path}\" not founded!", True)

        # Run interpretation.
        interpretator_run(cli_source)

        # Message.
        print(f"[Info] File \"{basename(cli_source_path)}\" was run!")
    elif cli_subcommand == "graph":
        # If this is graph subcommand.

        # Get source.
        cli_source, _ = load_source_from_file(cli_source_path)

        # File exists check.
        if cli_source is FileNotFoundError:
            cli_error_message("Error", f"File \"{cli_source_path}\" not founded!", True)

        # Generate graph file.
        graph_generate(cli_source, cli_source_path)

        # Message.
        print(f"[Info] .dot file \"{basename(cli_source_path)}.dot\" generated!")
    elif cli_subcommand == "python":
        # If this is python subcommand.

        # Get source.
        cli_source, cli_context = load_source_from_file(cli_source_path)

        # File exists check.
        if cli_source is FileNotFoundError:
            cli_error_message("Error", f"File \"{cli_source_path}\" not founded!", True)

        # Generate python file.
        python_generate(cli_source, cli_context, cli_source_path)

        # Message.
        print(f"[Info] .py file \"{basename(cli_source_path)}.py\" generated!")
    else:
        # If unknown subcommand.

        # Message.
        cli_usage_message(__file__)
        cli_error_message("Error", "Unknown subcommand `{cli_subcommand}`!")


if __name__ == "__main__":
    # Entry point.

    # CLI entry point.
    cli_entry_point()
