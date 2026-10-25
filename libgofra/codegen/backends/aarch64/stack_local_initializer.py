"""Assembly abstraction layer that hides declarative assembly OPs into functions that generates that for you."""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never

from libgofra.codegen.backends.aarch64.primitive_instructions import (
    AddressingMode,
    get_address_of_label,
    pop_cells_from_stack_into_registers,
    push_integer_onto_stack,
)
from libgofra.codegen.backends.frame import build_local_variables_frame_offsets
from libgofra.codegen.backends.initializer import (
    T_AnyVariableInitializer,
    VariableIntArrayInitializerValue,
    VariableIntFieldedStructureInitializerValue,
    VariableIntSliceInitializerValue,
    VariableStringPtrArrayInitializerValue,
    VariableStringPtrInitializerValue,
    literal_to_codegen_initializer,
)
from libgofra.types.composite.array import ArrayType
from libgofra.types.composite.pointer import PointerType

if TYPE_CHECKING:
    from collections.abc import Mapping

    from libgofra.codegen.backends.aarch64.writer import WriterProtocol
    from libgofra.codegen.backends.string_pool import StringPool
    from libgofra.hir.variable import Variable
    from libgofra.types._base import Type


def write_function_local_stack_variables_initializer(
    writer: WriterProtocol,
    string_pool: StringPool,
    *,
    local_variables: Mapping[str, Variable[Type]],
) -> None:
    local_offsets = build_local_variables_frame_offsets(local_variables)
    for variable in local_variables.values():
        if variable.initial_value is None:
            continue
        initializer = literal_to_codegen_initializer(
            variable.initial_value,
            target_type=variable.type,
        )

        current_offset = local_offsets.offsets[variable.name]
        _write_initializer_for_stack_variable(
            writer,
            initializer,
            string_pool,
            variable.type,
            current_offset,
        )


def _write_initializer_for_stack_variable(
    writer: WriterProtocol,
    initial_value: T_AnyVariableInitializer,
    string_pool: StringPool,
    var_type: Type,
    offset: int,
) -> None:
    assert offset > 0

    if isinstance(initial_value, int):
        return _set_local_numeric_var_immediate(
            writer,
            initial_value,
            var_type,
            offset,
        )

    if isinstance(initial_value, VariableIntArrayInitializerValue):
        assert isinstance(var_type, ArrayType)

        flat = var_type.flatten()
        for i, value in enumerate(initial_value.values):
            _set_local_numeric_var_immediate(
                writer,
                value,
                flat.element_type,
                offset=offset - flat.get_index_offset(i),
            )
        return None

    if isinstance(initial_value, VariableStringPtrInitializerValue):
        # Load string as static string and dispatch pointer on entry
        static_blob_sym = string_pool.add(initial_value.string)
        assert isinstance(var_type, PointerType)
        get_address_of_label(writer, "X0", static_blob_sym, mode=AddressingMode.PAGE)
        writer.instruction(f"str X0, [X29, -{offset}]")
        return None

    if isinstance(
        initial_value,
        VariableIntFieldedStructureInitializerValue
        | VariableStringPtrArrayInitializerValue
        | VariableIntSliceInitializerValue,
    ):  # pyright: ignore[reportUnnecessaryIsInstance]
        msg = f"{initial_value} is not implemented on-stack within codegen"
        raise NotImplementedError(msg)

    assert_never(initial_value)


def _set_local_numeric_var_immediate(
    writer: WriterProtocol,
    value: int,
    t: Type,
    offset: int,
) -> None:
    """Set immediate numeric value for local variable at given offset. Respects memory store instructions."""
    assert 0 < t.size_in_bytes <= 8, "Too big type to store into"

    # Type-to-register width rule (same as in `perform_operation_onto_stack`):
    # - widths up to 4 bytes use the W registers / half-word access
    # - 8-byte values use the X0 registers
    is_hword = t.size_in_bytes <= 4
    sr = ("XZR", "WZR")[is_hword] if value == 0 else ("X0", "W0")[is_hword]

    if sr in ("X0", "W0") and value != 0:
        if value.bit_length() <= 16:
            writer.instruction(f"mov {sr}, #{value}")
        else:
            push_integer_onto_stack(writer, value)
            pop_cells_from_stack_into_registers(writer, "X0")

    # Frame slots which lay far from the frame pointer may not be addressable
    # by an immediate offset of the store instruction, so always compute the
    # target address into X16 (the frame scratch register) and store indirectly.
    writer.instruction("mov X16, X29")
    writer.instruction(f"sub X16, X16, #{offset}")
    writer.instruction(f"str {sr}, [X16]")

