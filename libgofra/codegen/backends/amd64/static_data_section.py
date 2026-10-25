from collections.abc import Mapping

from libgofra.codegen.backends.amd64._context import AMD64CodegenContext
from libgofra.codegen.common.initializer import (
    parse_initializer,
)
from libgofra.codegen.common.string_pool import StringPool
from libgofra.codegen.sections._factory import SectionType
from libgofra.hir.variable import Variable
from libgofra.types._base import Type


def initialize_static_data_section(
    context: AMD64CodegenContext,
    static_strings: StringPool,
    static_variables: Mapping[str, Variable[Type]],
) -> None:
    """Initialize data section fields with given values.

    Section is an tuple (label, data)
    Data is an string (raw ASCII) or number (zeroed memory blob)
    TODO(@kirillzhosul, @stepanzubkov): Review alignment for data sections.
    """
    write_uninitialized_data_section(context, static_variables)
    write_initialized_data_section(context, static_strings, static_variables)
    # Must defined after others - string initializer may forward reference them
    # but we define them by single-pass within writing initializer
    write_text_string_section(context, static_strings, reference_suffix="d")


def write_initialized_data_section(
    context: AMD64CodegenContext,
    strings: StringPool,
    variables: Mapping[str, Variable[Type]],
) -> None:
    """Initialize data section fields with given values.

    Section is an tuple (label, data)
    Data is an string (raw ASCII) or number (zeroed memory blob)
    """
    variables = {k: v for k, v in variables.items() if v.initial_value is not None}

    if not variables and not strings:
        return

    context.section(SectionType.DATA)

    for name, variable in variables.items():
        _write_static_segment_const_variable_initializer(
            context,
            variable,
            symbol_name=name,
        )

    if not strings.is_empty():
        # 8 byte alignment for string descriptors
        context.fd.write(".align 8\n")

    for data, name in strings.items():
        # TODO: Proper alignment
        decoded_string = data.encode().decode("unicode_escape")
        length = len(decoded_string)
        context.fd.write(f"{name}: \n\t.quad {name}d\n\t.quad {length}\n")


def _get_ddd_for_type(t: Type) -> str:
    """Get Data Definition Directive for type based on byte size."""
    type_size = t.size_in_bytes
    if type_size <= 1:
        return ".byte"
    if type_size <= 2:
        return ".value"
    if type_size <= 4:
        return ".long"
    if type_size <= 8:
        return ".quad"
    msg = f"Cannot get DDD for symbol of type {t}, max byte size is capped"
    raise ValueError(msg)


def _write_static_segment_const_variable_initializer(
    context: AMD64CodegenContext,
    variable: Variable[Type],
    symbol_name: str,
) -> None:
    type_size = variable.size_in_bytes
    alignment = max(1, getattr(variable.type, "alignment", 1))
    align_exponent = alignment.bit_length() - 1
    context.fd.write(f".align {align_exponent}\n")

    assert variable.initial_value is not None
    plan = parse_initializer(variable.initial_value, variable.type)

    context.fd.write(f"{symbol_name}:\n")
    current_offset = 0
    for store in plan:
        if store.offset > current_offset:
            remaining = store.offset - current_offset
            context.fd.write(f"\t.zero {remaining}\n")
            current_offset = store.offset
        match store.kind:
            case "int":
                ddd = _get_ddd_for_type_size(store.size)
                assert store.int_value is not None
                context.fd.write(f"\t{ddd} {store.int_value}\n")
                current_offset += store.size
            case "string_ptr":
                assert store.string_value is not None
                context.fd.write(f"\t.quad {context.string_pool.add(store.string_value)}\n")
                current_offset += store.size
            case "padding":
                context.fd.write(f"\t.zero {store.size}\n")
                current_offset += store.size
            case "fill":
                context.fd.write(
                    f"\t.fill {store.fill_count}, {store.size}, {store.fill_value}\n",
                )
                context.comment_eol(f"Filler ({store.fill_value})")
                current_offset += store.size * store.fill_count
            case _:
                msg = f"Unsupported initializer store: {store}"
                raise ValueError(msg)

    if current_offset < type_size:
        remaining = type_size - current_offset
        context.fd.write(f"\t.zero {remaining}")
    context.fd.write("\n")



def _get_ddd_for_type_size(size_in_bytes: int) -> str:
    if size_in_bytes <= 1:
        return ".byte"
    if size_in_bytes <= 2:
        return ".value"
    if size_in_bytes <= 4:
        return ".long"
    return ".quad"


def write_uninitialized_data_section(
    context: AMD64CodegenContext,
    variables: Mapping[str, Variable[Type]],
) -> None:
    """Emit data section with uninitialized variables."""
    uninitialized_variables = {
        k: v for k, v in variables.items() if v.initial_value is None
    }

    if not uninitialized_variables:
        return

    context.section(SectionType.BSS)
    for name, variable in uninitialized_variables.items():
        type_size = variable.size_in_bytes
        assert type_size, f"Variables must have size (from {variable.name})"
        context.fd.write(f"{name}: .space {type_size}\n")


def write_text_string_section(
    context: AMD64CodegenContext,
    strings: StringPool,
    *,
    reference_suffix: str,
) -> None:
    """Emit text section with pure string text.

    :param reference_suffix: Append to each string symbol as it may overlap with real structure of string.
    """
    if strings.is_empty():
        return
    context.section(SectionType.STRINGS)
    for data, name in strings.items():
        context.fd.write(f'{name}{reference_suffix}: .asciz "{data}"\n')
