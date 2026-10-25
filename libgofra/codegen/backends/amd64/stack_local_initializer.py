"""AMD64 local stack variable initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never

from libgofra.codegen.common.frame import build_local_variables_frame_offsets
from libgofra.codegen.common.initializer import (
    InitializerStorePlan,
    parse_initializer,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from libgofra.codegen.backends.amd64._context import AMD64CodegenContext
    from libgofra.hir.variable import Variable
    from libgofra.types._base import Type
from libgofra.types.primitive.integers import I8Type, I16Type, I32Type, I64Type


def write_function_local_stack_variables_initializer(
    context: AMD64CodegenContext,
    *,
    local_variables: Mapping[str, Variable[Type]],
) -> None:
    local_offsets = build_local_variables_frame_offsets(local_variables)
    for variable in local_variables.values():
        initial_value = variable.initial_value
        if initial_value is None:
            continue

        current_offset = local_offsets.offsets[variable.name]
        plan = parse_initializer(initial_value, variable.type)
        _apply_initializer_plan(context, plan, current_offset)


def _apply_initializer_plan(
    context: AMD64CodegenContext,
    plan: tuple[InitializerStorePlan, ...],
    base_offset: int,
) -> None:
    assert base_offset > 0

    for store in plan:
        if store.kind == "int":
            _set_local_numeric_var_immediate(
                context,
                _type_for_size(store.size),
                base_offset - store.offset,
                store.int_value if store.int_value is not None else 0,
            )
        elif store.kind == "string_ptr":
            assert store.string_value is not None
        elif store.kind == "padding":
            continue
        elif store.kind == "fill":
            for i in range(store.fill_count):
                _set_local_numeric_var_immediate(
                    context,
                    _type_for_size(store.size),
                    base_offset - (store.offset + store.size * i),
                    store.fill_value,
                )
        else:
            assert_never(store.kind)

    # handle string ptr stores separately (need string_pool at context)
    string_stores = [s for s in plan if s.kind == "string_ptr"]
    for store in string_stores:
        assert store.string_value is not None
        context.write(
            f"leaq {context.string_pool.add(store.string_value)}(%rip), %rax",
            f"movq %rax, -{base_offset - store.offset}(%rbp)",
        )
    # no-op placeholder line retained for lint oddities only
    _ = context


def _type_for_size(size: int) -> Type:
    if size <= 1:
        return I8Type()
    if size <= 2:
        return I16Type()
    if size <= 4:
        return I32Type()
    return I64Type()


def _set_local_numeric_var_immediate(
    context: AMD64CodegenContext,
    t: Type,
    offset: int,
    value: int,
) -> None:
    assert 0 < t.size_in_bytes <= 8, "Too big type to store into"

    size = t.size_in_bytes
    if size == 1:
        reg = "%al"
        suf = "b"
    elif size == 2:
        reg = "%ax"
        suf = "w"
    elif size == 4:
        reg = "%eax"
        suf = "l"
    else:
        reg = "%rax"
        suf = "q"

    if value == 0:
        context.write(f"xor{suf} {reg}, {reg}")
    else:
        context.write(f"mov{suf} ${value}, {reg}")

    context.write(f"mov{suf} {reg}, {-offset}(%rbp)")
