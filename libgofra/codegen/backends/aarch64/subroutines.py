"""Assembly abstraction layer that hides declarative assembly OPs into functions that generates that for you."""

from __future__ import annotations

from typing import TYPE_CHECKING

from libgofra.codegen.backends.aarch64.abi_call_convention import (
    aarch64_abi_argument_target_registers,
    load_return_value_from_stack_into_abi_registers,
)
from libgofra.codegen.backends.aarch64.frame import (
    preserve_callee_frame,
    restore_callee_frame,
)
from libgofra.codegen.backends.aarch64.registers import AARCH64_STACK_ALIGNMENT_BIN
from libgofra.codegen.common.frame import build_local_variables_frame_offsets
from libgofra.types.primitive.floats import F32Type

from .primitive_instructions import (
    push_register_onto_stack,
)
from .stack_local_initializer import (
    write_function_local_stack_variables_initializer,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from libgofra.codegen.abi import AARCH64ABI
    from libgofra.codegen.backends.aarch64.writer import WriterProtocol
    from libgofra.codegen.common.string_pool import StringPool
    from libgofra.codegen.dwarf.dwarf import DWARF
    from libgofra.hir.function import Function
    from libgofra.hir.variable import Variable
    from libgofra.types._base import Type

DEFAULT_FUNCTIONS_ALIGNMENT = AARCH64_STACK_ALIGNMENT_BIN


def function_begin_with_prologue(  # noqa: PLR0913
    writer: WriterProtocol,
    abi: AARCH64ABI,
    string_pool: StringPool | None,
    *,
    name: str,
    global_name: str | None = None,
    preserve_frame: bool = True,
    is_naked: bool = False,
    local_variables: Mapping[str, Variable[Type]],
    parameters: Sequence[Type],
    dwarf: DWARF | None,
    dwarf_function: Function | None,
) -> None:
    """Begin an function symbol.

    Injects prologue with preparing required state (e.g registers, frame/stack pointers)

    :name: Symbol name of the function (as it is emitted as a label)
    :global_name: Mark that function symbol as global for linker
        (must be the very same symbol as `name`, otherwise it stays local)
    :preserve_frame: If true will preserve function state for proper stack management and return address
    :is_naked: If true the function has no prologue at all, so arguments are not
        pushed onto the operand stack (they are passed in registers per C ABI)
    """
    # TODO: Checkout `BTI` when i have an proper hardware
    # TODO: Checkout PAC because it is suddenly does not work rn

    if global_name:
        writer.directive("globl", global_name)

    alignment = (
        DEFAULT_FUNCTIONS_ALIGNMENT
        if writer.config.align_functions_bytes is None
        else writer.config.align_functions_bytes
    )
    if alignment > 1:
        if alignment % 2 == 0:
            writer.directive("p2align", alignment // 2)
        else:
            writer.directive("align", alignment)

    writer.label(name)
    if dwarf and dwarf_function:
        dwarf.trace_function_start(dwarf_function)
        dwarf.trace_source_location(dwarf_function.defined_at)

    if writer.config.dwarf_emit_cfi:
        writer.directive("cfi_startproc")

    if preserve_frame:
        local_offsets = build_local_variables_frame_offsets(local_variables)
        preserve_callee_frame(writer, local_space_size=local_offsets.local_space_size)

    if parameters and not is_naked:
        # Naked function has no prologue, so arguments stay in registers (per C ABI)
        # and the naked body reads them directly from there
        # Mapping must match ABI argument register allocation.
        param_sources = aarch64_abi_argument_target_registers(abi, parameters)

        fp_registers = set(getattr(abi, "fp_arguments_registers", ()))
        for param, src in zip(parameters, param_sources, strict=False):
            if src is None:
                continue
            if src in fp_registers:
                if isinstance(param, F32Type):
                    sreg = src.replace("D", "S")
                    writer.instruction(f"fmov W9, {sreg}")
                else:
                    writer.instruction(f"fmov X9, {src}")
                push_register_onto_stack(writer, "X9")
            else:
                push_register_onto_stack(writer, src)

    if not local_variables:
        return
    write_function_local_stack_variables_initializer(
        writer,
        string_pool,
        local_variables=local_variables,
    )


def function_return(
    writer: WriterProtocol,
    abi: AARCH64ABI,
    *,
    has_preserved_frame: bool = True,
    return_type: Type,
) -> None:
    """Return from an function.

    Emits proper epilogue to restore required state

    :has_preserved_frame: If true, will restore that to jump out and proper stack management
    """
    load_return_value_from_stack_into_abi_registers(abi, writer, t=return_type)

    if has_preserved_frame:
        restore_callee_frame(writer)

    writer.instruction("ret")


def function_end_with_epilogue(  # noqa: PLR0913
    writer: WriterProtocol,
    abi: AARCH64ABI,
    *,
    has_preserved_frame: bool,
    return_type: Type,
    is_early_return: bool,
    dwarf: DWARF | None,
    is_naked: bool = False,
) -> None:
    """End function with proper epilogue.

    Epilogue is required to proper restore required state (e.g registers, frame/stack pointers)
    and possibly cleanup.

    :has_preserved_frame: If true, will restore that to jump out and proper stack management
    :is_early_return: If true, will not emit end end of procedure symbol (e.g directly early return, not finish)
    """
    if not is_naked:
        function_return(
            writer,
            abi,
            has_preserved_frame=has_preserved_frame,
            return_type=return_type,
        )

    if dwarf:
        dwarf.trace_function_end()
    if not is_early_return and writer.config.dwarf_emit_cfi:
        writer.directive("cfi_endproc")
