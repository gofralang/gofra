from __future__ import annotations

from datetime import datetime
from typing import IO, TYPE_CHECKING, cast

from gofra.codegen.backends._context import CodegenContext
from gofra.codegen.backends.aarch64_macos.assembly import (
    AARCH64_ABI_REGISTERS,
    drop_cells_from_stack,
    evaluate_conditional_block_on_stack_with_jump,
    ipc_syscall_macos,
    pop_cells_from_stack_into_registers,
    pop_or_store_into_register,
    push_integer_onto_stack,
    push_static_address_onto_stack,
    store_integer_into_register,
)
from gofra.codegen.backends.aarch64_macos.registers import (
    AARCH64_MACOS_SYSCALL_NUMBER_REGISTER,
)
from gofra.parser.intrinsics import Intrinsic
from gofra.parser.operators import Operator, OperatorType
from gofra.typecheck.types import GofraType

if TYPE_CHECKING:
    from collections.abc import Sequence

    from gofra.context import ProgramContext


def generate_AARCH64_MacOS_backend(  # noqa: N802
    fd: IO[str],
    program_context: ProgramContext,
    *,
    debug_comments: bool,
) -> None:
    context = CodegenContext(fd=fd)

    if debug_comments:
        _write_debug_header_comment(context)

    # NOTICE: Linkage for extern function is not done in this backend
    # because it is not required for AARCH64 MacOS
    # (linker automatically links extern functions)

    _write_function_declarations(
        context,
        program_context,
        debug_comments=debug_comments,
    )

    _write_entry_header(fd)

    _write_executable_body_instruction_set(
        context,
        program_context.operators,
        program_context,
        debug_comments=debug_comments,
    )
    _write_program_epilogue(context, debug_comments=debug_comments)
    _write_static_segment(program_context, context)


def _write_executable_body_instruction_set(
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
                push_integer_onto_stack(context, operator.operand)
            case OperatorType.PUSH_STRING:
                assert isinstance(operator.operand, str)

                # String without interpolation
                raw_string = operator.token.text[1:-1]
                len_string = len(operator.operand)  # Interpolation folds bits
                static_segment = context.load_string(raw_string)

                push_static_address_onto_stack(context, segment=static_segment)
                push_integer_onto_stack(context, value=len_string)
            case OperatorType.DO:
                assert isinstance(operator.jumps_to_operator_idx, int)
                evaluate_conditional_block_on_stack_with_jump(
                    context,
                    jump_over_label=f".ctx_{operator.jumps_to_operator_idx}_over",
                )
            case OperatorType.IF:
                assert isinstance(operator.jumps_to_operator_idx, int)
                evaluate_conditional_block_on_stack_with_jump(
                    context,
                    jump_over_label=f".ctx_{operator.jumps_to_operator_idx}",
                )
            case OperatorType.END | OperatorType.WHILE:
                if isinstance(operator.jumps_to_operator_idx, int):
                    context.write("b .ctx_%s" % operator.jumps_to_operator_idx)
                    context.fd.write(f".ctx_{idx}_over:\n")
                else:
                    context.fd.write(f".ctx_{idx}:\n")
            case OperatorType.INTRINSIC:
                assert isinstance(operator.operand, Intrinsic)
                match operator.operand:
                    case Intrinsic.MEMORY_LOAD:
                        context.write(
                            "ldr X0, [SP]",
                            "ldr X0, [X0]",
                            "str X0, [SP]",
                        )
                    case Intrinsic.MEMORY_STORE:
                        context.write(
                            "ldr X0, [SP]",
                            "ldr X1, [SP, #16]",
                            "str X0, [X1]",
                            "add SP, SP, #32",
                        )
                    case Intrinsic.DROP:
                        # TODO(@kirillzhosul): Optimize (batch) multiple drop OPs into single shift for N bytes  # noqa: FIX002, TD003
                        drop_cells_from_stack(context, cells_count=1)
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

                        syscall_number = injected_args.pop()
                        pop_or_store_into_register(
                            context,
                            register=AARCH64_MACOS_SYSCALL_NUMBER_REGISTER,
                            integer_or_register=syscall_number,
                        )

                        store_retval_onto_stack = (
                            # Do not store result on stack if optimization is applied for omitting result
                            # this occurs when result drops after syscall
                            not operator.syscall_optimization_omit_result
                        )

                        assert syscall_arguments <= 8, "ABI registers count overflow"  # noqa: PLR2004
                        for arg_n in range(syscall_arguments - 1):
                            # Load register in reversed order of stack so top of the stack is max register
                            arg_register = syscall_arguments - arg_n - 2

                            injected_arg = injected_args[-arg_n] if arg_n else None
                            register = cast(
                                AARCH64_ABI_REGISTERS,
                                f"X{arg_register}",
                            )
                            if injected_arg is None:
                                pop_cells_from_stack_into_registers(context, register)
                            else:
                                store_integer_into_register(
                                    context,
                                    register,
                                    injected_arg,
                                )

                        ipc_syscall_macos(
                            context,
                            syscall_number=syscall_number,
                            store_retval_onto_stack=store_retval_onto_stack,
                        )
                    case Intrinsic.PLUS:
                        pop_cells_from_stack_into_registers(context, "X0", "X1")
                        context.write(
                            "add X0, X1, X0",
                            "sub SP, SP, #16",
                            "str X0, [SP]",
                        )
                    case Intrinsic.MINUS:
                        pop_cells_from_stack_into_registers(context, "X0")
                        context.write(
                            "sub X0, X1, X0",
                            "sub SP, SP, #16",
                            "str X0, [SP]",
                        )
                    case Intrinsic.COPY:
                        context.write(
                            "ldr X0, [SP]",
                            "str X0, [SP]",
                            "sub SP, SP, #16",
                            "str X0, [SP]",
                        )
                    case Intrinsic.INCREMENT:
                        context.write(
                            "ldr X0, [SP]",
                            "add X0, X0, #1",
                            "str X0, [SP]",
                        )
                    case Intrinsic.DECREMENT:
                        context.write(
                            "ldr X0, [SP]",
                            "sub X0, X0, #1",
                            "str X0, [SP]",
                        )
                    case Intrinsic.MULTIPLY:
                        pop_cells_from_stack_into_registers(context, "X0", "X1")
                        context.write(
                            "mul X0, X1, X0",
                            "sub SP, SP, #16",
                            "str X0, [SP]",
                        )
                    case Intrinsic.DIVIDE:
                        pop_cells_from_stack_into_registers(context, "X0", "X1")
                        context.write(
                            "sdiv X0, X1, X0",
                            "sub SP, SP, #16",
                            "str X0, [SP]",
                        )
                    case Intrinsic.MODULUS:
                        pop_cells_from_stack_into_registers(context, "X0", "X1")
                        context.write(
                            "udiv X2, X1, X0",
                            "mul X2, X2, X0",
                            "sub X0, X1, X2",
                            "sub SP, SP, #16",
                            "str X0, [SP]",
                        )
                    case Intrinsic.NOT_EQUAL:
                        pop_cells_from_stack_into_registers(context, "X1", "X0")
                        context.write(
                            "cmp X0, X1",
                            "cset X0, ne",
                            "sub SP, SP, #16",
                            "str X0, [SP]",
                        )
                    case Intrinsic.GREATER_EQUAL_THAN:
                        pop_cells_from_stack_into_registers(context, "X1", "X0")
                        context.write(
                            "cmp X0, X1",
                            "cset X0, ge",
                            "sub SP, SP, #16",
                            "str X0, [SP]",
                        )
                    case Intrinsic.LESS_EQUAL_THAN:
                        pop_cells_from_stack_into_registers(context, "X1", "X0")
                        context.write(
                            "cmp X0, X1",
                            "cset X0, le",
                            "sub SP, SP, #16",
                            "str X0, [SP]",
                        )
                    case Intrinsic.LESS_THAN:
                        pop_cells_from_stack_into_registers(context, "X1", "X0")
                        context.write(
                            "cmp X0, X1",
                            "cset X0, lt",
                            "sub SP, SP, #16",
                            "str X0, [SP]",
                        )
                    case Intrinsic.GREATER_THAN:
                        pop_cells_from_stack_into_registers(context, "X1", "X0")
                        context.write(
                            "cmp X0, X1",
                            "cset X0, gt",
                            "sub SP, SP, #16",
                            "str X0, [SP]",
                        )
                    case Intrinsic.EQUAL:
                        pop_cells_from_stack_into_registers(context, "X1", "X0")
                        context.write(
                            "cmp X0, X1",
                            "cset X0, eq",
                            "sub SP, SP, #16",
                            "str X0, [SP]",
                        )
                    case Intrinsic.SWAP:
                        pop_cells_from_stack_into_registers(context, "X0")
                        context.write(
                            "ldr X1, [SP]",  # optimize shifting as we push to the same cell
                            "str X0, [SP]",
                            "sub SP, SP, #16",
                            "str X1, [SP]",
                        )
            case OperatorType.CALL:
                assert isinstance(operator.operand, str)

                function_name = operator.operand
                function = program_context.functions[function_name]

                if function.is_externally_defined:
                    # @kirillzhosul: We are reversing arg registers loading end to start
                    # As loading head of the stack means loading the last argument
                    stack_offset = 0
                    for _, arg_register in zip(
                        range(len(function.type_contract_in)),
                        range(len(function.type_contract_in) - 1, -1, -1),
                    ):
                        arg_type = function.type_contract_in[arg_register]
                        match arg_type:
                            case GofraType.INTEGER:
                                context.write(
                                    "ldr W%s, [SP, #%i]" % (arg_register, stack_offset),
                                )
                                stack_offset += 16
                            case GofraType.POINTER:
                                context.write(
                                    "ldr X%s, [SP, #%i]" % (arg_register, stack_offset),
                                )
                                stack_offset += 16
                            case _:
                                raise NotImplementedError
                    context.write("add SP, SP, #%i" % (stack_offset))
                context.write("bl %s" % function_name)

                if function.type_contract_out:
                    # TODO(@kirillzhosul): No FFI reference for W%, and X% registers
                    context.write(
                        "sub SP, SP, #16",
                        "str X0, [SP]",
                    )
            case OperatorType.PUSH_MEMORY_POINTER:
                assert isinstance(operator.operand, str)
                push_static_address_onto_stack(context, operator.operand)
            case _:
                raise NotImplementedError(
                    "Operator %s is not implemented in AARCH64 MacOS backend"
                    % operator.type.name,
                )


def _write_debug_operator_comment(context: CodegenContext, operator: Operator) -> None:
    location = operator.token.location

    if operator.type == OperatorType.INTRINSIC:
        assert isinstance(operator.operand, Intrinsic)
        comment = "// * Intrinsic %s" % operator.operand.name
    else:
        comment = "// * Operator %s" % operator.type.name
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
            context,
            function.source,
            program_context,
            debug_comments=debug_comments,
        )
        context.write("ret")


def _write_debug_header_comment(context: CodegenContext) -> None:
    context.fd.write("// Assembly generated by Gofra codegen backend\n\n")
    context.fd.write("// Generated at: %s\n" % datetime.now(tz=None))  # noqa: DTZ005
    context.fd.write("// Target: AARCH64, MacOS\n\n")


def _write_program_epilogue(context: CodegenContext, *, debug_comments: bool) -> None:
    if debug_comments:
        context.write(
            "// Program epilogue ",
            "// (exit return-code 0)",
            "// (always included)",
        )
    context.write(
        "mov X0, #0",
        "mov X16, #1",
        "svc #0",
    )


def _write_static_segment(
    program_context: ProgramContext,
    context: CodegenContext,
) -> None:
    context.fd.write(".section __DATA,__data\n")
    for string_key, string_value in context.strings.items():
        context.fd.write(f'{string_key}: .asciz "{string_value}"\n')

    for memory_name, memory_segment_size in program_context.memories.items():
        context.fd.write("%s: .space %d\n" % (memory_name, memory_segment_size))


def _write_entry_header(fd: IO[str]) -> None:
    fd.write(".global _start\n")
    fd.write(".align 4\n\n")
    fd.write("_start:\n")
