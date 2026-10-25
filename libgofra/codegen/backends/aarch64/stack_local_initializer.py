"""AARCH64 local stack variable initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never

from libgofra.codegen.backends.aarch64.primitive_instructions import (
    AddressingMode,
    get_address_of_label,
    pop_cells_from_stack_into_registers,
    push_integer_onto_stack,
)
from libgofra.codegen.common.frame import build_local_variables_frame_offsets
from libgofra.codegen.common.initializer import (
    InitializerStorePlan,
    parse_initializer,
)
from libgofra.types.primitive.integers import I8Type, I16Type, I32Type, I64Type

if TYPE_CHECKING:
    from collections.abc import Mapping

    from libgofra.codegen.backends.aarch64.writer import WriterProtocol
    from libgofra.codegen.common.string_pool import StringPool
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
        current_offset = local_offsets.offsets[variable.name]
        plan = parse_initializer(variable.initial_value, variable.type)
        _apply_initializer_plan(
            writer,
            string_pool,
            plan,
            current_offset,
        )


def _apply_initializer_plan(
    writer: WriterProtocol,
    string_pool: StringPool,
    plan: tuple[InitializerStorePlan, ...],
    base_offset: int,
) -> None:
    assert base_offset > 0
    for store in plan:
        if store.kind == "int":
            _set_local_numeric_var_immediate(
                writer,
                store.int_value if store.int_value is not None else 0,
                _type_for_size(store.size),
                base_offset - store.offset,
            )
        elif store.kind == "string_ptr":
            assert store.string_value is not None
            static_blob_sym = string_pool.add(store.string_value)
            get_address_of_label(writer, "X0", static_blob_sym, mode=AddressingMode.PAGE)
            writer.instruction(
                f"str X0, [X29, -{base_offset - store.offset}]",
            )
        elif store.kind == "padding":
            continue
        elif store.kind == "fill":
            for i in range(store.fill_count):
                _set_local_numeric_var_immediate(
                    writer,
                    store.fill_value,
                    _type_for_size(store.size),
                    base_offset - (store.offset + store.size * i),
                )
        else:
            assert_never(store.kind)


def _type_for_size(size: int) -> Type:
    if size <= 1:
        return I8Type()
    if size <= 2:
        return I16Type()
    if size <= 4:
        return I32Type()
    return I64Type()


def _set_local_numeric_var_immediate(
    writer: WriterProtocol,
    value: int,
    t: Type,
    offset: int,
) -> None:
    """Set immediate numeric value for local variable at given offset. Respects memory store instructions."""
    assert 0 < t.size_in_bytes <= 8, "Too big type to store into"

    is_hword = t.size_in_bytes <= 4
    sr = ("XZR", "WZR")[is_hword] if value == 0 else ("X0", "W0")[is_hword]

    if sr in ("X0", "W0") and value != 0:
        if value.bit_length() <= 16:
            writer.instruction(f"mov {sr}, #{value}")
        else:
            push_integer_onto_stack(writer, value)
            pop_cells_from_stack_into_registers(writer, "X0")

    writer.instruction("mov X16, X29")
    writer.instruction(f"sub X16, X16, #{offset}")
    writer.instruction(f"str {sr}, [X16]")
