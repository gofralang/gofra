"""
    'Gofra' stack module.
    Contains stack class, that may be used for marking things that is stacks.
"""


class Stack:
    """
        Stack implementation for the language (More optional than useful).
    """
    __stack = None

    def __init__(self):
        """ Constructor. """
        self.__stack = list()

    def __len__(self):
        """ Length getter. """
        return len(self.__stack)

    def push(self, value):
        """ Push any value on the stack. """
        self.__stack.append(value)

    def pop(self):
        """ Pop any value from the stack. """
        return self.__stack.pop()
