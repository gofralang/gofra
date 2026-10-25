"""Assembly abstraction layer that hides declarative assembly OPs into functions that generates that for you."""

from __future__ import annotations

from typing import TYPE_CHECKING

from libgofra.codegen.backends.frame import build_local_variables_frame_offsets
from libgofra.codegen.float_bits import float_to_bits
from libgofra.exceptions import GofraError
from libgofra.hir.operator import OperatorType
from libgofra.types.primitive.void import VoidType

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from libgofra.hir.variable import Variable
    from libgofra.types._base import Type

    from ._context import AMD64CodegenContext
    from .registers import AMD64_GP_REGISTERS


def drop_cells_from_stack(context: AMD64CodegenContext, *, cells_count: int) -> None:
    """Drop stack cells from stack.

    Stack alignment should be review, but `popq` unlike `pop` will shift by 64 bits
    """
    assert cells_count > 0, "Tried to drop negative cells count from stack"
    for _ in range(cells_count):
        context.write("popq %rax")  # Use zero register?


def pop_cells_from_stack_into_registers(
    context: AMD64CodegenContext,
    *registers: AMD64_GP_REGISTERS,
) -> None:
    """Pop cells from stack and store into given registers.

    Stack alignment should be review, but probably this codegen ensure with `popq`/`pushq` that all cells are 64 bits
    """
    assert registers, "Expected registers to store popped result into!"

    for register in registers:
        context.write(f"popq %{register}")


def push_register_onto_stack(
    context: AMD64CodegenContext,
    register: AMD64_GP_REGISTERS,
) -> None:
    """Store given register onto stack under current stack pointer."""
    context.write(f"pushq %{register}")


def store_integer_into_register(
    context: AMD64CodegenContext,
    register: AMD64_GP_REGISTERS,
    value: int,
) -> None:
    """Store given value into given register (as QWORD)."""
    context.write(f"movq ${value}, %{register}")


def push_integer_onto_stack(
    context: AMD64CodegenContext,
    value: int,
) -> None:
    """Push given integer onto stack.

    TODO(@kirillzhosul, @stepanzubkov): Review max and etc like in AARCH64_MacOS
    """
    assert value.bit_count() <= 8 * 8, (
        "Can push only integers within 64 bits range (8 bytes, x64)"
    )
    is_negative = value < 0
    value = abs(value)

    store_integer_into_register(context, register="rax", value=value)
    if is_negative:
        context.write("neg %rax")
    push_register_onto_stack(context, register="rax")


def push_float_onto_stack(
    context: AMD64CodegenContext,
    value: float,
) -> None:
    """Push given floating point value onto stack as its raw 64-bit bits."""
    push_integer_onto_stack(context, float_to_bits(value))


def push_static_address_onto_stack(
    context: AMD64CodegenContext,
    segment: str,
) -> None:
    """Push executable static memory address onto stack with page dereference."""
    context.write(f"leaq {segment}(%rip), %rax")
    push_register_onto_stack(context, register="rax")


def ipc_syscall_linux(
    context: AMD64CodegenContext,
    *,
    arguments_count: int,
    store_retval_onto_stack: bool,
    injected_args: list[int | None] | None,
) -> None:
    """Call system (syscall) and apply IPC ABI convention to arguments."""
    assert not injected_args or len(injected_args) == arguments_count + 1
    assert context.target.operating_system != "Windows", (
        "Windows Syscall usage is discouraged"
    )

    if not injected_args:
        injected_args = [None for _ in range(arguments_count + 1)]

    abi = context.abi
    registers_to_load = (
        abi.syscall_number_register,
        *abi.syscall_arguments_registers[:arguments_count][::-1],
    )

    for injected_argument, register in zip(
        injected_args,
        registers_to_load,
        strict=False,
    ):
        if injected_argument is not None:
            # Register injected and inferred from stack
            store_integer_into_register(
                context,
                register=register,
                value=injected_argument,
            )
            continue
        pop_cells_from_stack_into_registers(context, register)

    if context.target.operating_system == "Darwin":
        # TODO: BSD/MACH kernel weirdness, must be implemented not in compiler itself?
        context.write("orq $0x2000000, %rax")

    context.write("syscall")

    if store_retval_onto_stack:
        # Mostly related to optimizations above if we dont want to store result
        push_register_onto_stack(context, abi.retval_primitive_64bit_register)



def amd64_abi_argument_target_registers(
    context: AMD64CodegenContext,
    parameters: Sequence[Type],
) -> list[str | None]:
    """Allocate (up to 6) integer and (up to 8) FP register names for parameters."""
    targets: list[str | None] = []
    int_i = 0
    fp_i = 0
    int_registers = context.abi.arguments_64bit_registers
    fp_registers = getattr(context.abi, "fp_arguments_registers", ())

    for param in parameters:
        if getattr(param, "is_fp", False):
            if fp_i < len(fp_registers):
                targets.append(fp_registers[fp_i])
            else:
                targets.append(None)
            fp_i += 1
        else:
            if int_i < len(int_registers):
                targets.append(int_registers[int_i])
            else:
                targets.append(None)
            int_i += 1

    return targets


def function_call(
    context: AMD64CodegenContext,
    *,
    name: str,
    type_contract_in: Sequence[Type],
    type_contract_out: Type,
) -> None:
    """Call an function using C ABI (Gofra native and C-FFI both functions).

    As Gofra under the hood uses C call convention for functions, this simplifies differences between C and Gofra calls.
    """
    i64_arguments_count = len(type_contract_in)
    store_return_value = not isinstance(type_contract_out, VoidType)

    if i64_arguments_count < 0:
        msg = f"Tried to call function `{name}` with negative arguments count"
        raise ValueError(msg)

    targets = amd64_abi_argument_target_registers(context, type_contract_in)

    for abi_register in reversed(targets):
        if abi_register is None:
            continue
        if abi_register.startswith("xmm"):
            context.write("popq %rax", f"movq %rax, %{abi_register}")
        else:
            context.write(f"popq %{abi_register}")

    if name.startswith("*"):
        # Function pointer call is not supported by this helper.
        raise NotImplementedError(name)
    context.write(
        f"callq {name}",
    )

    if store_return_value:
        if getattr(type_contract_out, "is_fp", False):
            context.write("movq %xmm0, %rax")
            push_register_onto_stack(context, "rax")
        else:
            push_register_onto_stack(
                context, context.abi.retval_primitive_64bit_register,
            )


def function_call_from_pointer(
    context: AMD64CodegenContext,
    *,
    register: AMD64_GP_REGISTERS,
    type_contract_in: Sequence[Type],
    type_contract_out: Type,
) -> None:
    """Call an indirect function pointer using AMD64 C ABI."""
    store_return_value = not isinstance(type_contract_out, VoidType)

    targets = amd64_abi_argument_target_registers(context, type_contract_in)

    for abi_register in reversed(targets):
        if abi_register is None:
            continue
        if abi_register.startswith("xmm"):
            context.write("popq %rax", f"movq %rax, %{abi_register}")
        else:
            context.write(f"popq %{abi_register}")

    context.write(
        f"callq *%{register}",
    )

    if store_return_value:
        if getattr(type_contract_out, "is_fp", False):
            context.write("movq %xmm0, %rax")
            push_register_onto_stack(context, "rax")
        else:
            push_register_onto_stack(context, context.abi.retval_primitive_64bit_register)


def push_local_variable_address_from_frame_offset(
    context: AMD64CodegenContext,
    local_variables: Mapping[str, Variable[Type]],
    local_variable: str,
) -> None:
    current_offset = build_local_variables_frame_offsets(
        local_variables,
    ).offsets[local_variable]

    context.write(
        "movq %rbp, %rax",
        f"subq ${current_offset}, %rax",
    )
    push_register_onto_stack(context, register="rax")


def store_into_memory_from_stack_arguments(
    context: AMD64CodegenContext,
    *,
    size_in_bytes: int,
) -> None:
    """Store value from into memory pointer, pointer and value acquired from stack."""
    pop_cells_from_stack_into_registers(context, "rax", "rbx")

    match size_in_bytes:
        case 1:
            context.write("movb %al, (%rbx)")
        case 2:
            context.write("movw %ax, (%rbx)")
        case 4:
            context.write("movl %eax, (%rbx)")
        case 8:
            context.write("movq %rax, (%rbx)")
        case _:
            msg = f"Unsupported store size: {size_in_bytes} bytes"
            raise GofraError(msg)


def load_memory_from_stack_arguments(
    context: AMD64CodegenContext,
    *,
    size_in_bytes: int = 8,
) -> None:
    """Load memory as value using arguments from stack."""
    pop_cells_from_stack_into_registers(context, "rax")

    match size_in_bytes:
        case 1:
            context.write("movzbq (%rax), %rax")
        case 2:
            context.write("movzwq (%rax), %rax")
        case 4:
            context.write("movslq (%rax), %rax")
        case 8:
            context.write("movq (%rax), %rax")
        case _:
            msg = f"Unsupported load size: {size_in_bytes} bytes"
            raise GofraError(msg)

    push_register_onto_stack(context, "rax")


def perform_operation_onto_stack(
    context: AMD64CodegenContext,
    operation: OperatorType,
    *,
    is_fp: bool = False,
) -> None:
    """Perform *math* operation onto stack (pop arguments and push back result)."""
    fp_arithmetic = {
        OperatorType.ARITHMETIC_PLUS: "addsd",
        OperatorType.ARITHMETIC_MINUS: "subsd",
        OperatorType.ARITHMETIC_MULTIPLY: "mulsd",
        OperatorType.ARITHMETIC_DIVIDE: "divsd",
    }
    fp_comparison = {
        OperatorType.COMPARE_EQUALS: "e",
        OperatorType.COMPARE_NOT_EQUALS: "ne",
        OperatorType.COMPARE_LESS: "b",
        OperatorType.COMPARE_GREATER: "a",
        OperatorType.COMPARE_LESS_EQUALS: "be",
        OperatorType.COMPARE_GREATER_EQUALS: "ae",
    }

    if is_fp and operation in fp_arithmetic:
        pop_cells_from_stack_into_registers(context, "rax", "rbx")
        context.write(
            "movq %rax, %xmm0",
            "movq %rbx, %xmm1",
            f"{fp_arithmetic[operation]} %xmm0, %xmm1",
            "movq %xmm1, %rax",
        )
        push_register_onto_stack(context, "rax")
        return

    if is_fp and operation in fp_comparison:
        pop_cells_from_stack_into_registers(context, "rax", "rbx")
        context.write(
            "movq %rax, %xmm0",
            "movq %rbx, %xmm1",
            "comisd %xmm0, %xmm1",
            f"set{fp_comparison[operation]} %al",
            "movzbq %al, %rax",
        )
        push_register_onto_stack(context, "rax")
        return

    registers = ("rbx", "rax")
    if operation == OperatorType.LOGICAL_NOT:
        registers = ("rax",)
    pop_cells_from_stack_into_registers(context, *registers)

    match operation:
        case OperatorType.ARITHMETIC_PLUS:
            context.write("addq %rbx, %rax")
        case OperatorType.ARITHMETIC_MINUS:
            context.write("subq %rbx, %rax")
        case OperatorType.ARITHMETIC_MULTIPLY:
            context.write("mulq %rbx")
        case OperatorType.ARITHMETIC_DIVIDE:
            context.write("cqo", "idivq %rbx")
        case OperatorType.ARITHMETIC_MODULUS:
            context.write("cqo", "idivq %rbx", "movq %rdx, %rax")
        case OperatorType.LOGICAL_NOT:
            context.write("notq %rax")
        case OperatorType.BITWISE_XOR:
            context.write("xorq %rbx, %rax")
        case OperatorType.LOGICAL_OR | OperatorType.BITWISE_OR:
            context.write("orq %rbx, %rax")
        case OperatorType.SHIFT_RIGHT:
            context.write("movq %rbx, %rcx", "shrq %cl, %rax")
        case OperatorType.SHIFT_LEFT:
            context.write("movq %rbx, %rcx", "shlq %cl, %rax")
        case OperatorType.BITWISE_AND | OperatorType.LOGICAL_AND:
            context.write("andq %rbx, %rax")
        case (
            OperatorType.COMPARE_EQUALS
            | OperatorType.COMPARE_GREATER
            | OperatorType.COMPARE_GREATER_EQUALS
            | OperatorType.COMPARE_LESS
            | OperatorType.COMPARE_NOT_EQUALS
            | OperatorType.COMPARE_LESS_EQUALS
        ):
            logic_op = {
                OperatorType.COMPARE_NOT_EQUALS: "ne",
                OperatorType.COMPARE_GREATER_EQUALS: "ge",
                OperatorType.COMPARE_LESS_EQUALS: "le",
                OperatorType.COMPARE_LESS: "l",
                OperatorType.COMPARE_GREATER: "g",
                OperatorType.COMPARE_EQUALS: "e",
            }
            context.write(
                "cmpq %rbx, %rax",
                f"set{logic_op[operation]}b %al",
                "movzx %al, %rax",
            )
        case _:
            msg = f"{operation} cannot be performed by codegen `{perform_operation_onto_stack.__name__}`"
            raise ValueError(msg)
    push_register_onto_stack(context, "rax")


def evaluate_conditional_block_on_stack_with_jump(
    context: AMD64CodegenContext,
    jump_over_label: str,
) -> None:
    """Evaluate conditional block by popping current value under SP against zero.

    If condition is false (value on stack) then jump out that conditional block to `jump_over_label`
    """
    pop_cells_from_stack_into_registers(context, "rax")
    context.write(
        "cmpq $0, %rax",
        f"je {jump_over_label}",
    )
