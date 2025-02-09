from datetime import datetime
from typing import IO, assert_never

from gofra.parser.intrinsics import Intrinsic
from gofra.parser.operators import Operator, OperatorType


def translate_assembly_arm_macos(fd: IO[str], operators: list[Operator]) -> None:
    _write_comment_header(fd)
    _write_entry_header(fd)

    idx, idx_end = 0, len(operators)
    static_segment: dict[str, str] = {}

    while idx < idx_end:
        operator = operators[idx]
        _write_operator_debug_comment(fd, operator)

        match operator.type:
            case OperatorType.PUSH_FLOAT:
                raise NotImplementedError
            case OperatorType.PUSH_INTEGER:
                fd.write("\tsub SP, SP, #16\n")
                fd.write(f"\tmov X0, #{operator.operand}\n")
                fd.write("\tstr X0, [SP]\n")
            case OperatorType.IF:
                assert isinstance(operator.operand, int)
                fd.write("\tldr X0, [SP]\n")
                fd.write("\tadd SP, SP, #16\n")

                fd.write("\tcmp X0, #1\n")
                fd.write(f"\tbne .ctx_{operator.operand - 1}\n")
            case OperatorType.END:
                assert isinstance(operator.operand, int)
                fd.write(f".ctx_{operator.operand}:\n")
            case OperatorType.PUSH_STRING:
                assert isinstance(operator.operand, str)
                static_string_buffer = f"string_{idx}"
                static_string_size = len(operator.operand)
                static_segment[static_string_buffer] = operator.token.text[1:-1]

                fd.write("\tsub SP, SP, #16\n")
                fd.write(f"\tadr X0, {static_string_buffer}\n")
                fd.write("\tstr X0, [SP]\n")

                fd.write("\tsub SP, SP, #16\n")
                fd.write(f"\tmov X0, #{static_string_size}\n")
                fd.write("\tstr X0, [SP]\n")

            case OperatorType.PUSH_SYMBOL:
                fd.write("\tsub SP, SP, #16\n")
                fd.write(f"\tmov X0, #{operator.operand}\n")
                fd.write("\tstr X0, [SP]\n")
            case OperatorType.INTRINSIC:
                assert isinstance(operator.operand, Intrinsic)
                match operator.operand:
                    case Intrinsic.FREE:
                        fd.write("\tadd SP, SP, #16\n")
                    case Intrinsic.EQUAL:
                        fd.write("\tldr X0, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")

                        fd.write("\tldr X1, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tcmp X0, X1\n")
                        fd.write("\tcset X0, eq\n")
                        fd.write("\tsub SP, SP, #16\n")
                        fd.write("\tstr X0, [SP]\n")

                    case Intrinsic.SWAP:
                        fd.write("\tldr X0, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")

                        fd.write("\tldr X1, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")

                        fd.write("\tsub SP, SP, #16\n")
                        fd.write("\tstr X0, [SP]\n")

                        fd.write("\tsub SP, SP, #16\n")
                        fd.write("\tstr X1, [SP]\n")
                    case Intrinsic.SWAP_OVER:
                        fd.write("\tldr X0, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")

                        fd.write("\tldr X1, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")

                        fd.write("\tldr X2, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")

                        fd.write("\tsub SP, SP, #16\n")
                        fd.write("\tstr X1, [SP]\n")

                        fd.write("\tsub SP, SP, #16\n")
                        fd.write("\tstr X2, [SP]\n")

                        fd.write("\tsub SP, SP, #16\n")
                        fd.write("\tstr X0, [SP]\n")
                    case Intrinsic.MINUS:
                        fd.write("\tldr X0, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")

                        fd.write("\tldr X1, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")

                        fd.write("\tsub X0, X1, X0\n")

                        fd.write("\tsub SP, SP, #16\n")
                        fd.write("\tstr X0, [SP]\n")
                    case Intrinsic.PLUS:
                        fd.write("\tldr X0, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")

                        fd.write("\tldr X1, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")

                        fd.write("\tadd X0, X1, X0\n")

                        fd.write("\tsub SP, SP, #16\n")
                        fd.write("\tstr X0, [SP]\n")
                    case Intrinsic.SYSCALL2:
                        fd.write("\tldr X16, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X0, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tsvc #0x80\n")
                    case Intrinsic.SYSCALL4:
                        fd.write("\tldr X16, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X2, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X1, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X0, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tsvc #0x80\n")
                    case Intrinsic.SYSCALL5:
                        fd.write("\tldr X16, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X3, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X2, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X1, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X0, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tsvc #0x80\n")
                    case Intrinsic.SYSCALL7:
                        fd.write("\tldr X16, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X5, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X4, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X3, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X2, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X1, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tldr X0, [SP]\n")
                        fd.write("\tadd SP, SP, #16\n")
                        fd.write("\tsvc #0x80\n")
                        fd.write("\tsub SP, SP, #16\n")
                        fd.write("\tstr X0, [SP]\n")
                    case _:
                        assert_never(operator.operand)
            case _:
                assert_never(operator.type)

        idx += 1

    _write_termination_epilogue(fd)
    _write_static_memory_segment(fd, static_segment)


def _write_operator_debug_comment(fd: IO[str], operator: Operator) -> None:
    location = operator.token.location

    if operator.type == OperatorType.INTRINSIC:
        assert isinstance(operator.operand, Intrinsic)
        fd.write(f"\t// * Intrinsic {operator.operand.name} ")
    else:
        fd.write(f"\t// * Operator {operator.type.name} ")
    fd.write(f"from {location[0]} at {location[1]}:{location[2]}")
    if operator.has_optimizations:
        fd.write(" [WAS OPTIMIZED AND FOLDED]")
    fd.write("\n")


def _write_static_memory_segment(fd: IO[str], static_strings: dict[str, str]) -> None:
    if not static_strings:
        return
    fd.write("// Static memory segment\n")
    fd.write("// Strings are statically injected for memory allocation later\n")
    for static_string_name, static_string_ascii in static_strings.items():
        fd.write(f'{static_string_name}: .asciz "{static_string_ascii}"\n')


def _write_termination_epilogue(fd: IO[str]) -> None:
    fd.write("\t// Entry termination epilogue (return-code 0)\n")
    fd.write("\tmov X0, #0\n")
    fd.write("\tmov X16, #1\n")
    fd.write("\tsvc #0\n")


def _write_entry_header(fd: IO[str]) -> None:
    fd.write(".global _start\n")
    fd.write(".align 4\n\n")
    fd.write("_start:\n")


def _write_comment_header(fd: IO[str]) -> None:
    fd.write("// Assembly generated by Gofra codegen backend\n\n")
    fd.write(f"// Generated at: {datetime.now()}\n")
    fd.write("// Target: ARM, MacOS\n\n")
