"""
    'Gofra' danger module.
    Contains classes, values and stuff like that.
    Should be refactored and totally removed later after refactoring.
"""

from typing import Optional, Union, Tuple, List, Dict
from enum import Enum, auto
from dataclasses import dataclass, field


class Stage(Enum):
    """ Enumeration for stage types. """
    LEXER = auto()
    PARSER = auto()
    LINTER = auto()
    RUNNER = auto()
    COMPILATOR = auto()


class Keyword(Enum):
    """ Enumeration for keyword types. """
    # Control flow.
    IF = auto()
    WHILE = auto()
    # Blocks.
    DO = auto()
    ELSE = auto()
    END = auto()
    # Other.
    MEMORY = auto()
    DEFINE = auto()


class Intrinsic(Enum):
    """ Enumeration for intrinsic types. """

    # Int (loops).
    # Increment (Undols to: 1 -) like x--.
    INCREMENT = auto()
    # Increment (Undols to: 1 +) like x++.
    DECREMENT = auto()

    # Int.
    PLUS = auto()  # +
    MINUS = auto()  # -
    MULTIPLY = auto()  # *
    DIVIDE = auto()  # /
    MODULUS = auto()  # %

    # Boolean.
    # ==, !=
    EQUAL = auto()
    NOT_EQUAL = auto()
    # <, >
    LESS_THAN = auto()
    GREATER_THAN = auto()
    # <=, >=
    LESS_EQUAL_THAN = auto()
    GREATER_EQUAL_THAN = auto()

    # Stack.
    COPY = auto()
    COPY_OVER = auto()
    COPY2 = auto()
    FREE = auto()
    SWAP = auto()

    # Memory.
    MEMORY_WRITE = auto()
    MEMORY_READ = auto()
    MEMORY_WRITE4BYTES = auto()
    MEMORY_READ4BYTES = auto()
    MEMORY_SHOW_CHARACTERS = auto()
    MEMORY_POINTER = auto()

    # I/O.
    IO_READ_INTEGER = auto()
    IO_READ_STRING = auto()
    # IO_WRITE = auto() -- Same as `show` / `mshowc`.

    # Utils.
    NULL = auto()
    SHOW = auto()


class TokenType(Enum):
    """ Enumeration for token types. """
    INTEGER = auto()
    CHARACTER = auto()
    STRING = auto()
    WORD = auto()
    KEYWORD = auto()

    # Exoteric.
    BYTECODE = auto()


class OperatorType(Enum):
    """ Enumeration for operaror types. """
    PUSH_INTEGER = auto()
    PUSH_STRING = auto()
    INTRINSIC = auto()

    # Keyword.
    IF = auto()
    WHILE = auto()
    DO = auto()
    ELSE = auto()
    END = auto()
    DEFINE = auto()
    MEMORY = auto()


# Types.

OPERAND = Optional[Union[int, str, Intrinsic]]
LOCATION = Tuple[str, int, int]
VALUE = Union[int, str, Keyword]

OPERATOR_ADDRESS = int
TYPE_INTEGER = int
TYPE_POINTER = int

# Memory.
MEMORY_MEMORIES_SIZE = 1024
MEMORY_BYTEARRAY_SIZE = 1024  # May be overwritten from directive #MEM_BUF_BYTE_SIZE={Size}!
MEMORY_MEMORIES_POINTER = MEMORY_BYTEARRAY_SIZE
MEMORY_BYTEARRAY_NULL_POINTER = 0


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
class Definition:
    """ Definition dataclass implementation. """
    # Location of the definition.
    location: LOCATION

    # List of tokens for definition.
    tokens: list[Token] = field(default_factory=list)


@dataclass
class Variable:
    """ Variable dataclass implementation. """
    name: str
    size: int
    ptr_offset: int


@dataclass
class Source:
    """ Source dataclass implementation. """

    # List of source operators.
    operators: List[Operator] = field(default_factory=list)


@dataclass
class ParserContext:
    """ Parser context dataclass implementation. """

    # Operators list.
    operators: List[Operator] = field(default_factory=list)

    # Memory stack.
    memory_stack: List[OPERATOR_ADDRESS] = field(default_factory=list)

    # Default bytearray size.
    memory_bytearray_size = MEMORY_BYTEARRAY_SIZE

    # Current parsing operator index.
    operator_index: OPERATOR_ADDRESS = 0

    # Directives.
    directive_linter_skip: bool = False
    directive_python_comments_skip: bool = False


# Other.

# Intrinsic names / types.
assert len(Intrinsic) == 28, "Please update INTRINSIC_NAMES_TO_TYPE after adding new Intrinsic!"
INTRINSIC_NAMES_TO_TYPE: Dict[str, Intrinsic] = {
    # Math.
    "+": Intrinsic.PLUS,
    "-": Intrinsic.MINUS,
    "*": Intrinsic.MULTIPLY,
    "/": Intrinsic.DIVIDE,
    "==": Intrinsic.EQUAL,
    "!=": Intrinsic.NOT_EQUAL,
    "<": Intrinsic.LESS_THAN,
    ">": Intrinsic.GREATER_THAN,
    ">=": Intrinsic.LESS_EQUAL_THAN,
    "<=": Intrinsic.GREATER_EQUAL_THAN,
    "%": Intrinsic.MODULUS,

    # Stack.
    "dec": Intrinsic.DECREMENT,
    "inc": Intrinsic.INCREMENT,
    "swap": Intrinsic.SWAP,
    "show": Intrinsic.SHOW,
    "copy": Intrinsic.COPY,
    "copy2": Intrinsic.COPY2,
    "copy_over": Intrinsic.COPY_OVER,
    "free": Intrinsic.FREE,

    # Memory.
    "mwrite": Intrinsic.MEMORY_WRITE,
    "mread": Intrinsic.MEMORY_READ,
    "mwrite4b": Intrinsic.MEMORY_WRITE4BYTES,
    "mread4b": Intrinsic.MEMORY_READ4BYTES,
    "mshowc": Intrinsic.MEMORY_SHOW_CHARACTERS,

    # I/O.
    "io_read_str": Intrinsic.IO_READ_STRING,
    "io_read_int": Intrinsic.IO_READ_INTEGER,

    # Constants*.
    "MPTR": Intrinsic.MEMORY_POINTER,
    "NULL": Intrinsic.NULL
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
assert len(Keyword) == 7, "Please update KEYWORD_NAMES_TO_TYPE after adding new Keyword!"
KEYWORD_NAMES_TO_TYPE: Dict[str, Keyword] = {
    "if": Keyword.IF,
    "else": Keyword.ELSE,
    "while": Keyword.WHILE,
    "do": Keyword.DO,
    "end": Keyword.END,
    "define": Keyword.DEFINE,
    "memory": Keyword.MEMORY
}
KEYWORD_TYPES_TO_NAME: Dict[Keyword, str] = {
    value: key for key, value in KEYWORD_NAMES_TO_TYPE.items()
}

assert len(Intrinsic) == 28, "Please update BYTECODE_INTRINSIC_NAMES_TO_OPERATOR_TYPE after adding new Intrinsic!"
BYTECODE_OPERATOR_NAMES_TO_INTRINSIC: Dict[str, Intrinsic] = {
    # Math.
    "+": Intrinsic.PLUS,
    "-": Intrinsic.MINUS,
    "*": Intrinsic.MULTIPLY,
    "/": Intrinsic.DIVIDE,
    "==": Intrinsic.EQUAL,
    "!=": Intrinsic.NOT_EQUAL,
    "<": Intrinsic.LESS_THAN,
    ">": Intrinsic.GREATER_THAN,
    ">=": Intrinsic.LESS_EQUAL_THAN,
    "<=": Intrinsic.GREATER_EQUAL_THAN,
    "%": Intrinsic.MODULUS,
    "--": Intrinsic.DECREMENT,
    "++": Intrinsic.INCREMENT,

    # Stack.
    "SW": Intrinsic.SWAP,
    "SH": Intrinsic.SHOW,
    "CP": Intrinsic.COPY,
    "CP2": Intrinsic.COPY2,
    "CPO": Intrinsic.COPY_OVER,
    "FR": Intrinsic.FREE,

    # Memory.
    "MW": Intrinsic.MEMORY_WRITE,
    "MR": Intrinsic.MEMORY_READ,
    "MW4": Intrinsic.MEMORY_WRITE4BYTES,
    "MR4": Intrinsic.MEMORY_READ4BYTES,
    "MSC": Intrinsic.MEMORY_SHOW_CHARACTERS,

    # I/O.
    "IORS": Intrinsic.IO_READ_STRING,
    "IORI": Intrinsic.IO_READ_INTEGER,

    # Constants*.
    "MPTR": Intrinsic.MEMORY_POINTER,
    "NULL": Intrinsic.NULL
}
INTRINSIC_TO_BYTECODE_OPERATOR: Dict[Intrinsic, str] = {
    value: key for key, value in BYTECODE_OPERATOR_NAMES_TO_INTRINSIC.items()
}
BYTECODE_OPERATOR_NAMES_TO_OPERATOR_TYPE: Dict[str, OperatorType] = {
    "I": OperatorType.PUSH_INTEGER,
}
OPERATOR_TYPE_TO_BYTECODE_OPERATOR: Dict[OperatorType, str] = {
    value: key for key, value in BYTECODE_OPERATOR_NAMES_TO_OPERATOR_TYPE.items()
}

# Extra `tokens`.
EXTRA_COMMENT = "//"
EXTRA_DIRECTIVE = "#"
EXTRA_CHAR = "'"
EXTRA_STRING = "\""
