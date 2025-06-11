from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import IO, Literal

from gofra.context import ProgramContext
from gofra.parser.intrinsics import Intrinsic
from gofra.parser.operators import Operator, OperatorType
from gofra.typecheck.types import GofraType

from ._context import CodegenContext


def generate_X86_Linux_backend(  # noqa: N802
    fd: IO[str],
    program_context: ProgramContext,
    *,
    debug_comments: bool,
) -> None:
    context = CodegenContext(fd=fd)

    if debug_comments:
        _write_debug_header_comment(context)

    # NOTICE: Linkage for extern function is not done in this backend
    # because it is not required for ARM64 MacOS
    # (linker automatically links extern functions)

    _write_function_declarations(
        context,
        program_context,
        debug_comments=debug_comments,
    )

    _write_entry_header(fd)

    _write_executable_body_instruction_set(
        fd,
        context,
        program_context.operators,
        program_context,
        debug_comments=debug_comments,
    )
    _write_program_epilogue(context, debug_comments=debug_comments)
    _write_static_segment(program_context, context)


def _write_executable_body_instruction_set(
    fd: IO[str],
    context: CodegenContext,
    operators: Sequence[Operator],
    program_context: ProgramContext,
    *,
    debug_comments: bool,
) -> None:
    for idx, operator in enumerate(operators):
        if debug_comments:
            _write_debug_operator_comment(context, operator)

        match operator.type:
            case OperatorType.PUSH_INTEGER:
                assert isinstance(operator.operand, int)
                _write_push_to_stack(
                    context,
                    operator.operand,
                    value_type="immediate",
                )
            case OperatorType.PUSH_STRING:
                assert isinstance(operator.operand, str)

                context.write(
                    "leaq %s, rax" % context.load_string(operator.token.text[1:-1]),
                    "pushq rax",
                    "movq $%d, rax" % len(operator.operand),
                    "pushq rax"
                )
            case OperatorType.DO:
                assert isinstance(operator.jumps_to_operator_idx, int)
                context.write(
                    "popq rax",
                    "cmpq $1, rax",
                    "jne .ctx_%s_over" % operator.jumps_to_operator_idx,
                )
            case OperatorType.END | OperatorType.WHILE:
                if isinstance(operator.jumps_to_operator_idx, int):
                    context.write(
                        "jmp .ctx_%s" % operator.jumps_to_operator_idx,
                    )
                    fd.write(f".ctx_{idx}_over:\n")
                else:
                    fd.write(f".ctx_{idx}:\n")
            case OperatorType.IF:
                assert isinstance(operator.jumps_to_operator_idx, int)
                context.write(
                    "popq rax",
                    "cmpq $1, rax",
                    "jne .ctx_%s" % operator.jumps_to_operator_idx,
                )
            case OperatorType.INTRINSIC:
                assert isinstance(operator.operand, Intrinsic)
                match operator.operand:
                    case Intrinsic.MEMORY_LOAD:
                        context.write(
                            "popq rax",
                            "movq (rax), rax",
                            "pushq rax",
                        )
                    case Intrinsic.MEMORY_STORE:
                        context.write(
                            "popq rax",
                            "popq rbx",
                            "movq rax, (rbx)",
                        )
                    case Intrinsic.DROP:
                        context.write("popq rax")
                    case (
                        Intrinsic.SYSCALL0
                        | Intrinsic.SYSCALL1
                        | Intrinsic.SYSCALL2
                        | Intrinsic.SYSCALL3
                        | Intrinsic.SYSCALL4
                        | Intrinsic.SYSCALL5
                        | Intrinsic.SYSCALL6
                    ):
                        syscall_arguments = operator.get_syscall_arguments_count()
                        injected_args = operator.syscall_optimization_injected_args or [
                            None for _ in range(syscall_arguments)
                        ]

                        # Load syscall number to proper register
                        if injected_args[-1] is None:
                            context.write(
                                "popq rax",
                            )
                        else:
                            context.write("movq $%d, rax" % injected_args[-1])

                        injected_args.pop()

                        for arg_n in range(syscall_arguments - 1):
                            # Load register in reversed order of stack so top of the stack is max register
                            arg_register = syscall_arguments - arg_n - 2

                            arg_register_name = ("rdi", "rsi", "rdx", "r10", "r8", "r9")[arg_register]
                            injected_arg = injected_args[-arg_n] if arg_n else None
                            if injected_arg is None:
                                context.write("popq %s" % arg_register_name)
                            else:
                                context.write(
                                    "movq $%d, %s" % (injected_arg, arg_register_name),
                                )
                        context.write("syscall")

                        if not operator.syscall_optimization_omit_result:
                            # Do not store result on stack if optimization is applied for omitting result
                            # this occurs when result drops after syscall
                            context.write(
                                "pushq rax",
                            )
                    case Intrinsic.PLUS:
                        context.write(
                            "popq rax",
                            "popq rbx",
                            "addq rbx, rax",
                            "pushq rax",
                        )
                    case Intrinsic.MINUS:
                        context.write(
                            "popq rax",
                            "popq rbx",
                            "subq rax, rbx",
                            "pushq rax",
                        )
                    case Intrinsic.COPY:
                        context.write(
                            "popq rax",
                            "pushq rax",
                            "pushq rax",
                        )
                    case Intrinsic.INCREMENT:
                        context.write(
                            "popq rax",
                            "incq rax",
                            "pushq rax",
                        )
                    case Intrinsic.DECREMENT:
                        context.write(
                            "popq rax",
                            "incq rax",
                            "pushq rax",
                        )
                    case Intrinsic.MULTIPLY:
                        context.write(
                            "popq rax",
                            "popq rbx",
                            "mulq rbx, rax",
                            "pushq rax",
                        )
                    case Intrinsic.DIVIDE:
                        context.write(
                            "popq rbx",
                            "popq rax",
                            "xorq rdx, rdx",
                            "idivq rbx",
                            "pushq rax",
                        )
                    case Intrinsic.MODULUS:
                        context.write(
                            "popq rbx",
                            "popq rax",
                            "xorq rdx, rdx",
                            "idivq rbx",
                            "pushq rdx",
                        )
                    case (
                        Intrinsic.NOT_EQUAL
                        | Intrinsic.GREATER_EQUAL_THAN
                        | Intrinsic.LESS_EQUAL_THAN
                        | Intrinsic.LESS_THAN
                        | Intrinsic.GREATER_THAN
                        | Intrinsic.EQUAL
                    ):
                        condition_suffix = {
                            Intrinsic.NOT_EQUAL: "ne",
                            Intrinsic.GREATER_EQUAL_THAN: "ge",
                            Intrinsic.LESS_EQUAL_THAN: "le",
                            Intrinsic.LESS_THAN: "l",
                            Intrinsic.GREATER_THAN: "g",
                            Intrinsic.EQUAL: "e",
                        }[operator.operand]

                        context.write(
                            "popq rbx",
                            "popq rax",
                            "cmpq rbx, rax",
                            "xorq rax, rax",
                            "set%sb al" % condition_suffix,
                            "pushq rax",
                        )
                    case Intrinsic.SWAP:
                        context.write(
                            "popq rax",
                            "popq rbx",
                            "pushq rax",
                            "pushq rbx",
                        )
            case OperatorType.CALL:
                assert isinstance(operator.operand, str)

                function_name = operator.operand
                function = program_context.functions[function_name]

                if function.is_externally_defined:
                    # @kirillzhosul: We are reversing arg registers loading end to start
                    # As loading head of the stack means loading the last argument
                    registers_64bit = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]
                    registers_32bit = ["edi", "esi", "edx", "ecx", "r8d", "r9d"]
                    for _, arg_register in zip(
                        range(len(function.type_contract_in)),
                        range(len(function.type_contract_in) - 1, -1, -1),
                    ):
                        arg_type = function.type_contract_in[arg_register]
                        match arg_type:
                            case GofraType.INTEGER:
                                context.write(
                                    "popq %s" % (registers_32bit[arg_register]),
                                )
                            case GofraType.POINTER:
                                context.write(
                                    "popq %s" % (registers_64bit[arg_register]),
                                )
                            case _:
                                raise NotImplementedError
                context.write("call %s" % function_name)

                if function.type_contract_out:
                    # TODO(@kirillzhosul): No FFI reference for W%, and X% registers
                    context.write(
                        "pushq rax",
                    )
            case OperatorType.PUSH_MEMORY_POINTER:
                assert isinstance(operator.operand, str)
                _write_push_to_stack(
                    context,
                    operator.operand,
                    value_type="address",
                )
            case _:
                raise NotImplementedError(
                    "Operator %s is not implemented in x86-64 Linux backend"
                    % operator.type.name,
                )


def _write_debug_header_comment(context: CodegenContext) -> None:
    context.fd.write("# Assembly generated by Gofra codegen backend\n\n")
    context.fd.write("# Generated at: %s\n" % datetime.now(tz=None))  # noqa: DTZ005
    context.fd.write("# Target: x86-64, Linux\n\n")


def _write_function_declarations(
    context: CodegenContext,
    program_context: ProgramContext,
    *,
    debug_comments: bool,
) -> None:
    for function in filter(
        lambda f: not f.emit_inline_body and not f.is_externally_defined,
        program_context.functions.values(),
    ):
        context.fd.write("%s:\n" % function.name)
        _write_executable_body_instruction_set(
            context.fd,
            context,
            function.source,
            program_context,
            debug_comments=debug_comments,
        )
        context.write("ret")


def _write_program_epilogue(context: CodegenContext, *, debug_comments: bool) -> None:
    if debug_comments:
        context.write(
            "# Program epilogue ",
            "# (exit return-code 0)",
            "# (always included)",
        )
    context.write(
        "movq $60, rax",
        "xorq rdi, rdi",
        "syscall",
    )


def _write_static_segment(
    program_context: ProgramContext,
    context: CodegenContext,
) -> None:
    for string_key, string_value in context.strings.items():
        context.fd.write(f'{string_key}: .string "{string_value}"\n')

    context.fd.write(".section .data\n")
    for memory_name, memory_segment_size in program_context.memories.items():
        context.fd.write("%s: .space %d\n" % (memory_name, memory_segment_size))


def _write_entry_header(fd: IO[str]) -> None:
    fd.write(".att_syntax noprefix\n")
    fd.write(".global _start\n")
    fd.write(".align 4\n\n")
    fd.write("_start:\n")


def _write_push_to_stack(
    context: CodegenContext,
    value: str | int,
    value_type: Literal["immediate", "register", "address"],
):
    if value_type == "immediate":
        context.write(f"movq ${value}, rax")
    elif value_type == "register":
        context.write(f"movq {value}, rax")
    elif value_type == "address":
        context.write(f"leaq {value}(rip), rax")
    else:
        raise ValueError("Unsupported value type")

    context.write("pushq rax")


def _write_debug_operator_comment(context: CodegenContext, operator: Operator) -> None:
    location = operator.token.location

    if operator.type == OperatorType.INTRINSIC:
        assert isinstance(operator.operand, Intrinsic)
        comment = "# * Intrinsic %s" % operator.operand.name
    else:
        comment = "# * Operator %s" % operator.type.name
    comment += " from %s" % location
    if operator.has_optimizations:
        if operator.is_syscall():
            comment += " [optimized, omit result: %s, injected args: %s]" % (
                operator.syscall_optimization_omit_result,
                operator.syscall_optimization_injected_args,
            )
        else:
            comment += " [optimized, infer type: %s]" % (
                operator.infer_type_after_optimization.name
                if operator.infer_type_after_optimization
                else "as-is"
            )

    context.write(comment)
