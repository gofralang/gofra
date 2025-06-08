"""Assembly abstraction layer that hides declarative assembly OPs into functions that generates that for you."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .registers import (
    AARCH64_ABI_REGISTERS,
    AARCH64_DOUBLE_WORD_BITS,
    AARCH64_GOFRA_TEMP_REGISTER,
    AARCH64_GP_REGISTERS,
    AARCH64_HALF_WORD_BITS,
    AARCH64_IPC_REGISTERS,
    AARCH64_MACOS_SYSCALL_NUMBER_REGISTER,
    AARCH64_MACOS_SYSCALL_RETVAL_REGISTER,
    AARCH64_SP,
    AARCH64_STACK_ALIGNMENT,
)

if TYPE_CHECKING:
    from gofra.codegen.backends._context import CodegenContext


def drop_cells_from_stack(context: CodegenContext, *, cells_count: int) -> None:
    """Drop stack cells from stack by shifting stack pointer (SP) by N bytes.

    Stack must be aligned so we use `AARCH64_STACK_ALIGNMENT`
    """
    assert cells_count > 0, "Tried to drop negative cells count from stack"
    stack_pointer_shift = AARCH64_STACK_ALIGNMENT * cells_count
    context.write(f"add {AARCH64_SP}, {AARCH64_SP}, #{stack_pointer_shift}")


def pop_cells_from_stack_into_registers(
    context: CodegenContext,
    *registers: AARCH64_ABI_REGISTERS | AARCH64_IPC_REGISTERS,
) -> None:
    """Pop cells from stack and store into given registers.

    Each cell is 8 bytes, but stack pointer is always adjusted by `AARCH64_STACK_ALIGNMENT` bytes
    to preserve stack alignment.
    """
    assert registers, "Expected registers to store popped result into!"

    pairs_count = 2

    total = len(registers)
    pairs = total // pairs_count

    for i in range(pairs):
        register_idx = i * pairs_count
        register_a, register_b = registers[register_idx : register_idx + pairs_count]
        context.write(
            f"ldp {register_a}, {register_b}, [{AARCH64_SP}], #{AARCH64_STACK_ALIGNMENT}",
        )

    if total % pairs_count != 0:
        # One register left (odd number of total registers)
        register = registers[-1]
        context.write(
            f"ldr {register}, [{AARCH64_SP}]",
            f"add {AARCH64_SP}, {AARCH64_SP}, #{AARCH64_STACK_ALIGNMENT}",
        )


def push_register_onto_stack(
    context: CodegenContext,
    register: AARCH64_ABI_REGISTERS | AARCH64_IPC_REGISTERS,
) -> None:
    """Store given register onto stack under current stack pointer."""
    context.write(f"str {register}, [{AARCH64_SP}, -{AARCH64_STACK_ALIGNMENT}]!")


def store_integer_into_register(
    context: CodegenContext,
    register: AARCH64_ABI_REGISTERS | AARCH64_IPC_REGISTERS,
    value: int,
) -> None:
    """Store given value into given register."""
    context.write(f"mov {register}, #{value}")


def push_integer_onto_stack(
    context: CodegenContext,
    value: int,
) -> None:
    """Push given integer onto stack with auto shifting less-significant bytes.

    Value must be less than 16 bytes (18_446_744_073_709_551_615).
    Negative numbers is dissalowed.

    TODO(@kirillzhosul): Negative numbers IS dissalowed:
        Consider using signed two complement representation with sign bit (highest bit) set
    """
    assert value >= 0, "Tried to push negative integer onto stack!"
    assert value <= AARCH64_DOUBLE_WORD_BITS, (
        "Tried to push integer that exceeding 16 bytes (64 bits register)."
    )

    if value <= AARCH64_HALF_WORD_BITS:
        # We have small immediate value which we may just store without shifts
        context.write(f"mov {AARCH64_GOFRA_TEMP_REGISTER}, #{value}")
        push_register_onto_stack(context, register=AARCH64_GOFRA_TEMP_REGISTER)
        return

    preserve_bits = False
    for shift in range(0, 64, 16):
        chunk = hex((value >> shift) & AARCH64_HALF_WORD_BITS)
        if chunk == "0x0":
            # Zeroed chunk so we dont push it as register is zerod
            continue

        if not preserve_bits:
            # Store upper bits
            context.write(f"movz {AARCH64_GOFRA_TEMP_REGISTER}, #{chunk}, lsl #{shift}")
            preserve_bits = True
            continue

        # Store lower bits
        context.write(f"movk {AARCH64_GOFRA_TEMP_REGISTER}, #{chunk}, lsl #{shift}")

    push_register_onto_stack(context, register=AARCH64_GOFRA_TEMP_REGISTER)


def push_static_address_onto_stack(
    context: CodegenContext,
    segment: str,
) -> None:
    """Push executable static memory addresss onto stack with page dereference."""
    context.write(
        f"adrp {AARCH64_GOFRA_TEMP_REGISTER}, {segment}@PAGE",
        f"add {AARCH64_GOFRA_TEMP_REGISTER}, {AARCH64_GOFRA_TEMP_REGISTER}, {segment}@PAGEOFF",
    )
    push_register_onto_stack(context, register=AARCH64_GOFRA_TEMP_REGISTER)


def evaluate_conditional_block_on_stack_with_jump(
    context: CodegenContext,
    jump_over_label: str,
) -> None:
    """Evaluate conditional block by popping current value under SP againts zero.

    If condition is false (value on stack) then jump out that conditional block to `jump_over_label`
    """
    pop_cells_from_stack_into_registers(context, AARCH64_GOFRA_TEMP_REGISTER)
    context.write(
        f"cmp {AARCH64_GOFRA_TEMP_REGISTER}, #0",
        f"beq {jump_over_label}",
    )


def pop_or_store_into_register(
    context: CodegenContext,
    register: AARCH64_GP_REGISTERS,
    integer_or_register: int | None,
) -> None:
    """Pop integer from stack and store into register or store integer directly into register if not None."""
    if integer_or_register is None:
        pop_cells_from_stack_into_registers(context, register)
    else:
        store_integer_into_register(
            context,
            register,
            integer_or_register,
        )


def ipc_syscall_macos(
    context: CodegenContext,
    *,
    syscall_number: int | None,
    store_retval_onto_stack: bool,
) -> None:
    """Call system (syscall) via supervisor call and apply IPC ABI convention to arguments."""
    # If we got predefined syscall number we will use that otherwise acquire that from stack

    # Supervisor call (syscall)
    context.write("svc #0")

    if store_retval_onto_stack:
        # Mostly related to optimizations above if we dont want to store result
        push_register_onto_stack(context, AARCH64_MACOS_SYSCALL_RETVAL_REGISTER)
