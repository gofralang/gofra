"""
    'Gofra' dump module.
    Contains all stuff releated to the dumping with human-readable format.
"""

from .danger import *


def __str_enum_class(instance: object):
    """
    Str
    :param: instance The instance to convert.
    """
    return str(instance)[len(f"{type(instance).__name__}."):]


def __dump_operator(operator: Operator, index: int):
    """
    Prints operator in human-readable format.
    :param: operator The operator to dump.
    :param: index The index of the operator.
    """
    if operator.type == OperatorType.INTRINSIC:
        readable_operator_type = __str_enum_class(operator.operand)
        readable_operator = f"${readable_operator_type}, {operator.operand}"
    else:
        readable_operator_type = __str_enum_class(operator.type)
        readable_operator = f"@{readable_operator_type}, {operator.operand}"

    print(f"index {index}, {readable_operator}")


def dump(operators: List[Operator]):
    """
        Prints all operators from given list in human-readable format.
        :param: operators List of operators.
    """
    assert len(operators) > 0, "List of operators should be not empty!"
    for index, operator in enumerate(operators):
        __dump_operator(operator, index)
