from enum import IntEnum, auto


class Keyword(IntEnum):
    IF = auto()
    WHILE = auto()
    DO = auto()
    ELSE = auto()
    END = auto()
    MACRO = auto()


WORD_TO_KEYWORD = {
    "if": Keyword.IF,
    "else": Keyword.ELSE,
    "while": Keyword.WHILE,
    "do": Keyword.DO,
    "end": Keyword.END,
    "macro": Keyword.MACRO,
}
KEYWORD_TO_NAME = {v: k for k, v in WORD_TO_KEYWORD.items()}
