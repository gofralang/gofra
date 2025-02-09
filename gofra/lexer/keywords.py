from enum import IntEnum, auto


class Keyword(IntEnum):
    IF = auto()
    WHILE = auto()
    DO = auto()
    ELSE = auto()
    END = auto()


WORD_TO_KEYWORD = {
    "if": Keyword.IF,
    "else": Keyword.ELSE,
    "while": Keyword.WHILE,
    "do": Keyword.DO,
    "end": Keyword.END,
}
