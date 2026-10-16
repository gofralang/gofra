from collections.abc import Sequence
from typing import TYPE_CHECKING, assert_never

from libgofra.codegen.abi import AARCH64ABI
from libgofra.codegen.backends.aarch64.abi_call_convention import (
    function_abi_call_by_symbol,
    function_abi_call_from_register,
)
from libgofra.codegen.backends.aarch64.frame import (
    push_local_variable_address_from_frame_offset,
)
from libgofra.codegen.backends.aarch64.primitive_instructions import (
    AddressingMode,
    compare_registers_boolean,
    drop_stack_slots,
    evaluate_conditional_block_on_stack_with_jump,
    jump_to_label,
    load_memory_from_stack_arguments,
    perform_operation_onto_stack,
    place_software_trap,
    pop_cells_from_stack_into_registers,
    push_address_of_label_onto_stack,
    push_float_onto_stack,
    push_integer_onto_stack,
    push_register_onto_stack,
    store_into_memory_from_stack_arguments,
)
from libgofra.codegen.backends.aarch64.registers import AARCH64_STACK_ALIGNMENT
from libgofra.codegen.backends.aarch64.subroutines import function_return
from libgofra.codegen.backends.aarch64.svc_syscall import ipc_aarch64_syscall
from libgofra.codegen.backends.aarch64.writer import WriterProtocol
from libgofra.codegen.backends.general import CODEGEN_GOFRA_CONTEXT_LABEL
from libgofra.codegen.backends.string_pool import StringPool
from libgofra.codegen.dwarf.dwarf import DWARF
from libgofra.exceptions import GofraError
from libgofra.hir.function import Function
from libgofra.hir.module import Module
from libgofra.hir.operator import (
    FunctionCallOperand,
    Operator,
    OperatorType,
    TypecastMeta,
)
from libgofra.hir.variable import VariableStorageClass
from libgofra.types import CharType, PointerType, Type
from libgofra.types.comparison import is_primitive_type
from libgofra.types.composite.function import FunctionType

if TYPE_CHECKING:
    from libgofra.codegen.backends.aarch64.registers import AARCH64_GP_REGISTERS


def _push_variable_address(
    writer: WriterProtocol,
    owner_function: Function,
    variable: str,
) -> None:
    if variable in owner_function.variables:
        hir_local_variable = owner_function.variables[variable]
        assert hir_local_variable.is_function_scope
        if hir_local_variable.storage_class != VariableStorageClass.STACK:
            msg = "Non stack local variables storage class is not implemented yet"
            raise NotImplementedError(msg)
        push_local_variable_address_from_frame_offset(
            writer,
            owner_function.variables,
            variable,
        )
        return

    # Global variable or memory
    push_address_of_label_onto_stack(writer, label=variable)


def aarch64_instruction_set(  # noqa: PLR0913, PLR0917
    writer: WriterProtocol,
    abi: AARCH64ABI,
    string_pool: StringPool,
    operators: Sequence[Operator],
    program: Module,
    owner_function: Function,
    dwarf: DWARF | None,
) -> None:
    """Write executable instructions from given operators."""
    writer.comment_eol(
        f"{owner_function.name} = {owner_function.parameters} -> {owner_function.return_type}",
    )

    for idx, operator in enumerate(operators):
        aarch64_operator_instructions(
            writer,
            abi,
            string_pool,
            operator,
            program,
            idx,
            owner_function,
            dwarf=dwarf,
        )


def aarch64_operator_instructions(  # noqa: PLR0913, PLR0917
    writer: WriterProtocol,
    abi: AARCH64ABI,
    string_pool: StringPool,
    operator: Operator,
    program: Module,
    idx: int,
    owner_function: Function,
    dwarf: DWARF | None,
) -> None:
    # TODO(@kirillzhosul): Assumes Apple aapcs64
    if dwarf:
        dwarf.trace_source_location(operator.location)

    match operator.type:
        case OperatorType.PUSH_VARIABLE_ADDRESS:
            assert isinstance(operator.operand, str)
            _push_variable_address(writer, owner_function, variable=operator.operand)
        case OperatorType.PUSH_INTEGER:
            assert isinstance(operator.operand, int)
            push_integer_onto_stack(writer, operator.operand)
        case OperatorType.PUSH_FLOAT:
            assert isinstance(operator.operand, float)
            push_float_onto_stack(writer, operator.operand)
        case OperatorType.CONDITIONAL_DO | OperatorType.CONDITIONAL_IF:
            assert isinstance(operator.jumps_to_operator_idx, int)
            label = CODEGEN_GOFRA_CONTEXT_LABEL % (
                owner_function.name,
                operator.jumps_to_operator_idx,
            )

            evaluate_conditional_block_on_stack_with_jump(writer, label)
        case OperatorType.CONDITIONAL_ELSE:
            assert isinstance(operator.jumps_to_operator_idx, int)
            label = CODEGEN_GOFRA_CONTEXT_LABEL % (
                owner_function.name,
                operator.jumps_to_operator_idx,
            )
            jump_to_label(writer, label)
            label = CODEGEN_GOFRA_CONTEXT_LABEL % (owner_function.name, idx)
            writer.label(label)
        case (
            OperatorType.CONDITIONAL_END
            | OperatorType.CONDITIONAL_WHILE
            | OperatorType.CONDITIONAL_FOR
        ):
            # This also should be refactored into `assembly` layer
            label = CODEGEN_GOFRA_CONTEXT_LABEL % (owner_function.name, idx)
            if isinstance(operator.jumps_to_operator_idx, int):
                label_to = CODEGEN_GOFRA_CONTEXT_LABEL % (
                    owner_function.name,
                    operator.jumps_to_operator_idx,
                )
                writer.instruction(f"b {label_to}")
            writer.label(label)
        case OperatorType.PUSH_STRING:
            assert isinstance(operator.operand, str)
            string_raw = str(operator.token.text[1:-1])
            label = string_pool.add(string_raw)
            push_address_of_label_onto_stack(writer, label)
        case OperatorType.FUNCTION_RETURN:
            function_return(
                writer,
                abi=abi,
                has_preserved_frame=True,
                return_type=owner_function.return_type,
            )
        case OperatorType.FUNCTION_CALL:
            assert isinstance(operator.operand, FunctionCallOperand)

            function = program.resolve_function_dependency(
                operator.operand.module,
                operator.operand.get_name(),
            )
            assert function is not None, (
                f"Cannot find function symbol `{operator.operand.get_name()}` in module '{operator.operand.module}' (current: {program.path}), will emit linkage error"
            )

            function_abi_call_by_symbol(
                writer,
                abi,
                name=function.name,
                parameters=function.parameter_types,
                return_type=function.return_type,
                call_convention="apple_aapcs64",
            )
        case OperatorType.STATIC_TYPE_CAST:
            assert operator.tc_meta
            assert isinstance(operator.tc_meta, TypecastMeta)

            meta = operator.tc_meta

            if meta.kind == TypecastMeta.Kind.REINTERPRET:
                return
            match meta.kind:
                case TypecastMeta.Kind.EXTEND:
                    pop_cells_from_stack_into_registers(writer, "X0")
                    size = meta.a.size_in_bytes
                    signed = not isinstance(meta.a, CharType)
                    match (size, signed):
                        case (1, True):
                            writer.instruction("sxtb X0, W0")
                        case (1, False):
                            writer.instruction("uxtb W0, W0")
                        case (2, True):
                            writer.instruction("sxth X0, W0")
                        case (2, False):
                            writer.instruction("uxth W0, W0")
                        case (4, True):
                            writer.instruction("sxtw X0, W0")
                        case (4, False):
                            writer.instruction("mov W0, W0")
                        case _:
                            msg = f"Truncate to {size}-byte not supported"
                            raise GofraError(msg)
                    push_register_onto_stack(writer, "X0")
                case TypecastMeta.Kind.TRUNCATE:
                    pop_cells_from_stack_into_registers(writer, "X0")
                    size = meta.b.size_in_bytes
                    signed = not isinstance(meta.b, CharType)
                    match (size, signed):
                        case (1, True):
                            writer.instruction("sxtb X0, W0")
                        case (1, False):
                            writer.instruction("uxtb W0, W0")
                        case (2, True):
                            writer.instruction("sxth X0, W0")
                        case (2, False):
                            writer.instruction("uxth W0, W0")
                        case (4, True):
                            writer.instruction("sxtw X0, W0")
                        case (4, False):
                            writer.instruction("mov W0, W0")
                        case _:
                            msg = f"Truncate to {size}-byte not supported"
                            raise GofraError(msg)
                    push_register_onto_stack(writer, "X0")
                case TypecastMeta.Kind.NORMALIZE_BOOL:
                    pop_cells_from_stack_into_registers(writer, "X0")
                    compare_registers_boolean(
                        writer,
                        register_a="X0",
                        register_b_or_immediate=0,
                        register="X0",
                        condition="ne",
                    )
                    push_register_onto_stack(writer, "X0")
                case _:
                    msg = f"{meta.a} -> {meta.b} cast via {meta.kind.name}"
                    raise NotImplementedError(msg)
        case OperatorType.STACK_DROP:
            drop_stack_slots(writer, slots_count=1)
        case OperatorType.STACK_COPY:
            writer.instruction("ldr X0, [SP]")
            writer.instruction(f"str X0, [SP, #-{AARCH64_STACK_ALIGNMENT}]!")

        case OperatorType.STACK_SWAP:
            pop_cells_from_stack_into_registers(writer, "X0", "X1")
            push_register_onto_stack(writer, "X0")
            push_register_onto_stack(writer, "X1")
        case (
            OperatorType.ARITHMETIC_MINUS
            | OperatorType.ARITHMETIC_PLUS
            | OperatorType.ARITHMETIC_MULTIPLY
            | OperatorType.ARITHMETIC_DIVIDE
            | OperatorType.ARITHMETIC_MODULUS
            | OperatorType.COMPARE_NOT_EQUALS
            | OperatorType.COMPARE_GREATER_EQUALS
            | OperatorType.COMPARE_LESS_EQUALS
            | OperatorType.COMPARE_LESS
            | OperatorType.COMPARE_GREATER
            | OperatorType.COMPARE_EQUALS
            | OperatorType.LOGICAL_NOT
            | OperatorType.LOGICAL_AND
            | OperatorType.LOGICAL_OR
            | OperatorType.BITWISE_AND
            | OperatorType.BITWISE_OR
            | OperatorType.SHIFT_LEFT
            | OperatorType.SHIFT_RIGHT
            | OperatorType.BITWISE_XOR
        ):
            perform_operation_onto_stack(
                writer,
                operation=operator.type,
            )
        case OperatorType.SYSCALL:
            assert isinstance(operator.operand, int)
            ipc_aarch64_syscall(
                writer,
                abi=abi,
                arguments_count=operator.operand,
                store_retval_onto_stack=True,
                injected_args=None,
            )
        case OperatorType.MEMORY_VARIABLE_READ:
            assert operator.tc_meta
            assert isinstance(operator.tc_meta, Type)
            assert operator.tc_meta.size_in_bytes <= 8, operator.token.location

            read_size = operator.tc_meta.size_in_bytes
            load_memory_from_stack_arguments(writer, size_in_bytes=read_size)
        case OperatorType.MEMORY_VARIABLE_WRITE:
            assert operator.tc_meta
            assert isinstance(operator.tc_meta, Type)
            assert operator.tc_meta.size_in_bytes <= 8, operator.token.location

            store_size = operator.tc_meta.size_in_bytes
            store_into_memory_from_stack_arguments(writer, size_in_bytes=store_size)
        case OperatorType.PUSH_VARIABLE_VALUE:
            assert isinstance(operator.operand, str)
            assert operator.tc_meta
            assert isinstance(operator.tc_meta, Type)
            # TODO(@kirillzhosul): This was merged from two operations - must be refactored (and also optimized)
            _push_variable_address(writer, owner_function, operator.operand)
            load_size = operator.tc_meta.size_in_bytes
            load_memory_from_stack_arguments(writer, size_in_bytes=load_size)
        case OperatorType.LOAD_PARAM_ARGUMENT:
            assert isinstance(operator.operand, str)

            param_ref = owner_function.parameter_map[operator.operand]
            _ = param_ref.initializer

            # TODO(@kirillzhosul): This was merged from two operations - must be refactored (and also optimized)
            _push_variable_address(writer, owner_function, operator.operand)

            # swap stack
            pop_cells_from_stack_into_registers(writer, "X0", "X1")
            push_register_onto_stack(writer, "X0")
            push_register_onto_stack(writer, "X1")

            # TODO: must use tc meta
            assert is_primitive_type(param_ref.type) or isinstance(
                param_ref.type,
                PointerType | FunctionType,
            ), param_ref.type
            store_into_memory_from_stack_arguments(
                writer,
                size_in_bytes=param_ref.type.size_in_bytes,
            )
        case OperatorType.DEBUGGER_BREAKPOINT:
            place_software_trap(
                writer,
                code=0xDEAD,
            )
        case OperatorType.INLINE_RAW_ASM:
            assert isinstance(operator.operand, str)
            for line in operator.operand.splitlines():
                writer.instruction(line)
        case OperatorType.STRUCT_FIELD_OFFSET:
            assert isinstance(operator.operand, tuple)
            struct, field = operator.operand
            field_offset = struct.get_field_offset(field)
            if field_offset:
                # only relatable as operation is pointer is not already at first structure field
                pop_cells_from_stack_into_registers(
                    writer,
                    "X0",
                )  # struct pointer (*struct)
                writer.instruction(f"add X0, X0, #{field_offset}")
                push_register_onto_stack(writer, "X0")
        case OperatorType.COMPILE_TIME_ERROR:
            ...  # Linter / typechecker
        case OperatorType.FUNCTION_CALL_FROM_STACK_POINTER:
            assert isinstance(operator.operand, FunctionType)
            call_like = operator.operand
            ptr_reg: AARCH64_GP_REGISTERS = "X10"
            pop_cells_from_stack_into_registers(writer, ptr_reg)
            function_abi_call_from_register(
                writer,
                abi,
                register=ptr_reg,
                parameters=call_like.parameters,
                return_type=call_like.return_type,
                call_convention="apple_aapcs64",
            )
        case OperatorType.PUSH_FUNCTION_POINTER:
            assert isinstance(operator.operand, FunctionCallOperand)
            callee = program.resolve_function_dependency(
                operator.operand.module,
                operator.operand.get_name(),
            )
            assert callee

            if callee.attrs.external:
                addressing_mode = AddressingMode.EXTERNAL
            elif callee.outer_function == owner_function:
                # TODO(@kirillzhosul): Must be NEAR for memory optimization
                # but got broken at some time? reverted to PAGE
                addressing_mode = AddressingMode.PAGE
            else:
                addressing_mode = AddressingMode.PAGE

            push_address_of_label_onto_stack(
                writer,
                label=f"_{callee.name}",
                temp_register="X0",
                mode=addressing_mode,
            )
        case _:
            assert_never(operator.type)
