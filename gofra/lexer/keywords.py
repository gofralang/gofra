from enum import IntEnum, auto


class Keyword(IntEnum):
    """Words that are related to language due to internal implementation like loops or parsing stage."""

    IF = auto()

    WHILE = auto()
    DO = auto()

    END = auto()

    INCLUDE = auto()
    MACRO = auto()

    EXTERN = auto()
    INLINE = auto()
    FUNCTION = auto()
    CALL = auto()


WORD_TO_KEYWORD = {
    "if": Keyword.IF,
    "while": Keyword.WHILE,
    "do": Keyword.DO,
    "end": Keyword.END,
    "include": Keyword.INCLUDE,
    "macro": Keyword.MACRO,
    "extern": Keyword.EXTERN,
    "call": Keyword.CALL,
    "func": Keyword.FUNCTION,
    "inline": Keyword.INLINE,
}
KEYWORD_TO_NAME = {v: k for k, v in WORD_TO_KEYWORD.items()}
