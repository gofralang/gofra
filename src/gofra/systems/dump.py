"""
    'Gofra' dump module.
    Contains all stuff releated to the dumping with human-readable format.
"""

from ..core.danger import *


def __dump_operator(operator: Operator, index: int):
    """
    Prints operator in human-readable format.
    :param operator: The operator to dump.
    :param index: The index of the operator.
    """
    if operator.type == OperatorType.INTRINSIC:
        readable_operator_name = operator.operand.name
        readable_operator = f"${readable_operator_name}"
    else:
        readable_operator_type = operator.type.name
        readable_operator = f"@{readable_operator_type}, {operator.operand}"

    print(f"index {index}, {readable_operator}")


def dump(operators: List[Operator]):
    """
        Prints all operators from given list in human-readable format.
        :param operators: List of operators.
    """
    assert len(operators) > 0, "List of operators should be not empty!"
    for index, operator in enumerate(operators):
        __dump_operator(operator, index)
