# MSPL Source Code.
# "Most Simple|Stupid Programming Language".

# Dataclass.
from dataclasses import dataclass, field

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
    pass


class Intrinsic(Enum):
    """ Enumeration for intrinsic types. """
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()


class TokenType(Enum):
    """ Enumeration for token types. """
    INTEGER = auto()
    WORD = auto()
    KEYWORD = auto()


class OperatorType(Enum):
    """ Enumeration for operaror types. """
    PUSH_INTEGER = auto()
    INTRINSIC = auto()


# Types.

# Operand.
OPERAND = Optional[Union[int, Intrinsic]]

# Location.
LOCATION = Tuple[str, int, int]

# Value.
VALUE = Union[int, str, Keyword]

# Other.

# Intrinsic names / types.
INTRINSIC_NAMES_TO_TYPE: Dict[str, Intrinsic] = {
    "+": Intrinsic.PLUS,
    "-": Intrinsic.MINUS,
    "*": Intrinsic.MULTIPLY,
}
INTRINSIC_TYPES_TO_NAME: Dict[Intrinsic, str] = {
    value: key for key, value in INTRINSIC_NAMES_TO_TYPE.items()
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

    # Context
    operators: List[Operator] = field(default_factory=list)


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

    # Check that there is no new operator type.
    assert len(OperatorType) == 2, "[lexer_tokenize()] Переполнение операторов!"

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

                    NAMES = (

                    )

                    if current_token_text in NAMES:
                        # If this is keyword.

                        # Return keyword token.
                        yield Token(
                            type=TokenType.KEYWORD,
                            text=current_token_text,
                            location=current_location,
                            value=NAMES[current_token_text]
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

    # Check that there is no new operator type.
    assert len(OperatorType) == 2, "[parser_parse()] Переполнение операторов!"

    # Reverse tokens.
    reversed_tokens: List[Token] = list(reversed(tokens))

    while len(reversed_tokens) > 0:
        # While there is any token.

        # Get current token.
        current_token = reversed_tokens.pop()

        if current_token.type == TokenType.WORD:
            # If we got a word.

            # Type check.
            assert isinstance(current_token.value, str), \
                "[parser_parse()] Неожиданный тип значения токена при парсинге (Ошибка лексера?)!"

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
        elif current_token.type == TokenType.INTEGER:
            # If we got a integer.

            # Type check.
            assert isinstance(current_token.value, int), \
                "[parser_parse()] Неожиданный тип значения токена при парсинге (Ошибка лексера?)!"

            # Create operator.
            operator = Operator(
                type=OperatorType.PUSH_INTEGER,
                token=current_token,
                operand=current_token.value
            )

            # Add operator to the context.
            context.operators.append(operator)
        elif current_token.type == TokenType.KEYWORD:
            # If we got a keyword.

            pass
        else:
            # If unknown operator type.
            assert False, f"[parser_parse()] Получен неизвестный оператор при парсинге! [НЕДОСЯГАЕМЫЙ БЛОК]"


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
    assert len(OperatorType) == 2, "Too much operator types!"

    # Check that there is no new instrinsic type.
    assert len(Intrinsic) == 3, "Too much intrinsics types!"

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
            else:
                # If unknown instrinsic type.
                assert False, "Unknown instrinsic! (How?)"
        else:
            # If unknown operator type.
            assert False, "Unknown operator type! (How?)"


# Graph.

def graph_generate(source: Source, path: str):
    """ Generates graph from the source. """

    # Open file.
    file = open(path + ".dot", "w")

    # Get source operators count.
    operators_count = len(source.operators)

    # Current operator index from the source.
    current_operator_index = 0

    # Check that there is no new operator type.
    assert len(OperatorType) == 2, "Too much operator types!"

    # Check that there is no new instrinsic type.
    assert len(Intrinsic) == 3, "Too much intrinsics types!"

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
            assert isinstance(current_operator.operand, int), "Type error, lexer level error?"

            # Write node data.
            file.write(f"   Operator_{current_operator_index} [label=PUSH_{current_operator.operand}];\n")
            file.write(f"   Operator_{current_operator_index} -> Operator_{current_operator_index + 1};\n")
        elif current_operator.type == OperatorType.INTRINSIC:
            # Intrinsic operator.

            # Type check.
            assert isinstance(current_operator.operand, Intrinsic), f"Type error, lexer level error?"

            # Write node data.
            file.write(f"   Operator_{current_operator_index} [label={repr(repr(INTRINSIC_TYPES_TO_NAME[current_operator.operand]))}];\n")
            file.write(f"   Operator_{current_operator_index} -> Operator_{current_operator_index + 1};\n")
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


if __name__ == "__main__":
    # Entry point.

    # CLI Options.
    cli_source_path = f"{getcwd()}\\" + "examples\\example.mspl"
    cli_subcommand = "interpretate"

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

        # Generate graph file.
        graph_generate(parser_context_source, cli_source_path)

        # Message.
        print(f"[Info] .dot file \"{basename(cli_source_path)}.dot\" generated!")

    else:
        # If unknown subcommand.

        # Message.
        print("[Error] Sorry, you entered unknown subcommand!")
