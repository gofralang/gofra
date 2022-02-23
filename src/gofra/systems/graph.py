"""
    'Gofra' graph module.
    Contains all stuff releated to the generating graph file from the source.
"""

from typing import IO
from os.path import basename

from ..core.danger import *
from ..core.other import try_open_file

# Constants.
__GRAPH_EXTENSION = ".dot"


def __write_header(file: IO, name: str):
    """
    Writes directed graph header that starts graph to the file.
    :param: file IO to write in.
    :param: name String of the header (graph) name.
    """
    file.write(f"digraph {name}" + "{\n")
    file.write(f"\tEntry [label=\"Entry Point\"];\n")
    file.write(f"\tEntry -> Operator_0;\n")


def __write_footer(file: IO, exit_operator_index: int):
    """
    Writes graph footer that closes graph to the file.
    :param: file IO to write in.
    :param: exit_operator_index Index of the last operator index, should be equals to the length of the source operators.
    """
    file.write(f"\tOperator_{exit_operator_index} [label=\"Exit Point\"];\n")
    file.write("}\n")


def __write_operator(file: IO, source: Source, operator: Operator, index: int):
    if operator.type == OperatorType.PUSH_INTEGER:
        assert isinstance(operator.operand, int), "Type error, parser level error?"

        file.write(f"   Operator_{index} [label=INT {operator.operand}];\n")
        file.write(f"   Operator_{index} -> Operator_{index + 1};\n")
    elif operator.type == OperatorType.PUSH_STRING:
        assert isinstance(operator.operand, str), "Type error, parser level error?"

        file.write(f"   Operator_{index} [label={repr(repr(operator.operand))}];\n")
        file.write(f"   Operator_{index} -> Operator_{index + 1};\n")
    elif operator.type == OperatorType.INTRINSIC:
        assert isinstance(operator.operand, Intrinsic), f"Type error, parser level error?"

        label = repr(repr(INTRINSIC_TYPES_TO_NAME[operator.operand]))
        file.write(f"   Operator_{index} [label={label}];\n")
        file.write(f"   Operator_{index} -> Operator_{index + 1};\n")
    elif operator.type == OperatorType.IF:
        assert isinstance(operator.operand, OPERATOR_ADDRESS), f"Type error, parser level error?"

        file.write(f"   Operator_{index} [shape=record label=if];\n")

        file.write(f"    Operator_{index} -> Operator_{index + 1} "
                   f"[label=true];\n")
        file.write(f"    Operator_{index} -> Operator_{operator.operand} "
                   f"[label=false];\n")
    elif operator.type == OperatorType.ELSE:
        assert isinstance(operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

        file.write(f"   Operator_{index} [shape=record label=else];\n")
        file.write(f"   Operator_{index} -> Operator_{operator.operand};\n")
    elif operator.type == OperatorType.WHILE:
        file.write(f"    Operator_{index} [shape=record label=while];\n")
        file.write(f"    Operator_{index} -> Operator_{index + 1};\n")
    elif operator.type == OperatorType.DO:
        assert isinstance(operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

        end_operator_index = source.operators[operator.operand].operand
        assert isinstance(end_operator_index, OPERATOR_ADDRESS), "Type error, parser level error?"

        file.write(f"    Operator_{index} [shape=record label=do];\n")

        file.write(f"    Operator_{index} -> Operator_{index + 1} "
                   f"[label=true];\n")
        file.write(f"    Operator_{index} -> Operator_{end_operator_index - 1} "
                   f"[label=false];\n")
    elif operator.type == OperatorType.END:
        assert isinstance(operator.operand, OPERATOR_ADDRESS), "Type error, parser level error?"

        file.write(f"   Operator_{index} [shape=record label=end];\n")
        file.write(f"   Operator_{index} -> Operator_{index + 1};\n")
    elif operator.type == OperatorType.DEFINE:
        assert False, "Got definition operator at runner stage, parser level error?"
    else:
        assert False, "Unknown operator type! "


def write(source: Source, path: str):
    """
    Generates graph `.dot` file from given source
    :
    """

    assert len(OperatorType) == 9, "Graph converting does not supports current operator types!"
    assert len(source.operators), "Source operators list should be not empty!"

    path = path + ("" if path.endswith(__GRAPH_EXTENSION) else __GRAPH_EXTENSION)
    file, _ = try_open_file(path, "w", True)
    __write_header(file, basename(path))

    for index, operator in enumerate(source.operators):
        __write_operator(
            *(file, source),
            *(operator, index)
        )

    __write_footer(file, len(source.operators))
    file.close()
