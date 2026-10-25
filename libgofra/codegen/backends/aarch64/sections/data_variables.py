from __future__ import annotations

from typing import TYPE_CHECKING, Literal, assert_never

from libgofra.codegen.common.initializer import (
    parse_initializer,
)
from libgofra.codegen.common.mangling import mangle_hir_symbol_name
from libgofra.codegen.sections._factory import SectionType

if TYPE_CHECKING:
    from collections.abc import Mapping

    from libgofra.codegen.backends.aarch64.writer import WriterProtocol
    from libgofra.codegen.common.string_pool import StringPool
    from libgofra.hir.variable import Variable
    from libgofra.types._base import Type


def write_initialized_data_section(
    writer: WriterProtocol,
    strings: StringPool,
    variables: Mapping[str, Variable[Type]],
) -> None:
    """Initialize data section fields with given values.

    Section is an tuple (label, data)
    Data is an string (raw ASCII) or number (zeroed memory blob)
    """
    variables = {k: v for k, v in variables.items() if v.initial_value is not None}

    if not variables and strings.is_empty():
        return

    writer.section(SectionType.DATA)
    alignment = None
    for variable in variables.values():
        if variable.type.alignment != alignment:
            writer.directive("align", variable.type.alignment)
            alignment = variable.type.alignment
        _write_static_segment_variable_initializer(
            writer,
            variable,
            string_pool=strings,
        )

    if not strings.is_empty():
        # 8 byte alignment for string descriptors
        writer.directive("align", 8)

    for data, name in strings.items():
        # TODO: Proper constant name mangling for string
        decoded_string = data.encode().decode("unicode_escape")
        length = len(decoded_string)
        writer.label(name)
        writer.sym_sect_directive("quad", f"{name}d")
        writer.sym_sect_directive("quad", length)


def _write_static_segment_variable_initializer(
    writer: WriterProtocol,
    variable: Variable[Type],
    string_pool: StringPool,
) -> None:
    type_size = variable.size_in_bytes
    assert type_size, (
        f"Variable {variable.name} defined at {variable.defined_at} has zero byte size (type {variable.type}) this variable will be not defined as symbol!"
    )

    symbol_name = mangle_hir_symbol_name(variable)

    assert variable.initial_value is not None
    plan = parse_initializer(
        variable.initial_value,
        variable.type,
    )

    writer.label(symbol_name)
    current_offset = 0
    for store in plan:
        if store.offset > current_offset:
            writer.sym_sect_directive("zero", store.offset - current_offset)
            current_offset = store.offset

        match store.kind:
            case "int":
                ddd = _ddd_for_size(store.size)
                assert store.int_value is not None
                writer.sym_sect_directive(ddd, store.int_value)
                current_offset += store.size
            case "string_ptr":
                assert store.string_value is not None
                writer.sym_sect_directive("quad", string_pool.add(store.string_value))
                current_offset += store.size
            case "padding":
                writer.sym_sect_directive("zero", store.size)
                current_offset += store.size
            case "fill":
                writer.sym_sect_directive(
                    "fill",
                    store.fill_count,
                    store.size,
                    store.fill_value,
                )
                writer.comment_eol(f"Filler ({store.fill_value})")
                current_offset += store.size * store.fill_count
            case _:
                assert_never(store.kind)

    if current_offset < type_size:
        writer.sym_sect_directive("zero", type_size - current_offset)


def _ddd_for_size(size_in_bytes: int) -> Literal["byte", "short", "word", "quad"]:
    if size_in_bytes <= 1:
        return "byte"
    if size_in_bytes <= 2:
        return "short"
    if size_in_bytes <= 4:
        return "word"
    return "quad"
