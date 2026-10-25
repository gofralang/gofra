from dataclasses import dataclass
from typing import Literal

from libgofra.codegen.common.float_bits import float32_to_bits, float_to_bits
from libgofra.hir.literals import (
    ArrayLiteral,
    BooleanLiteral,
    CharacterLiteral,
    FloatLiteral,
    IntegerLiteral,
    Literal_T,
    StringLiteral,
    StructureLiteral,
)
from libgofra.types import ArrayType, BoolType, CharType, PointerType, Type
from libgofra.types.composite import StringType, StructureType
from libgofra.types.primitive.floats import F32Type, F64Type
from libgofra.types.primitive.integers import (
    IntegerType,
)


@dataclass(frozen=True, slots=True)
class InitializerStorePlan:
    """One flattened, layout-resolved piece of an initialized variable."""

    offset: int
    size: int
    kind: Literal["int", "string_ptr", "padding", "fill"]
    int_value: int | None = None
    string_value: str | None = None
    fill_count: int = 0
    fill_value: int = 0


type InitializerPlan = tuple[InitializerStorePlan, ...]


def _primitive_scalar_plan(
    literal: Literal_T,
    target_type: Type,
) -> InitializerStorePlan | None:
    """Return a scalar plan when the literal/type combination is scalar."""
    match (literal, target_type):
        case (
            IntegerLiteral(value=v) | CharacterLiteral(value=v),
            IntegerType() | CharType() | BoolType(),
        ):
            return InitializerStorePlan(
                offset=0,
                size=target_type.size_in_bytes,
                kind="int",
                int_value=v,
            )
        case (BooleanLiteral(value=v), BoolType()):
            return InitializerStorePlan(
                offset=0,
                size=target_type.size_in_bytes,
                kind="int",
                int_value=int(v),
            )
        case (FloatLiteral(value=v), F64Type()):
            return InitializerStorePlan(
                offset=0,
                size=8,
                kind="int",
                int_value=float_to_bits(v),
            )
        case (FloatLiteral(value=v), F32Type()):
            return InitializerStorePlan(
                offset=0,
                size=4,
                kind="int",
                int_value=float32_to_bits(v),
            )
        case (StringLiteral(value=s), PointerType(points_to=StringType())):
            return InitializerStorePlan(
                offset=0,
                size=target_type.size_in_bytes,
                kind="string_ptr",
                string_value=s,
            )
    return None


def parse_initializer(
    literal: Literal_T,
    target_type: Type,
    base_offset: int = 0,
) -> InitializerPlan:
    """Parse an HIR literal into a layout-resolved atomic plan."""
    scalar = _primitive_scalar_plan(literal, target_type)
    if scalar is not None:
        return (_replace_offset(scalar, base_offset),)

    stores: list[InitializerStorePlan] = []
    match (literal, target_type):
        case (ArrayLiteral(elements=elements, default=filler), ArrayType()):
            flat_target = target_type.flatten()
            nested_array = bool(elements) and all(
                isinstance(e, ArrayLiteral) for e in elements
            )

            if nested_array:
                element_type = target_type.element_type
                present_count = len(elements)
                outer_stride = element_type.size_in_bytes
                used_bytes = 0
                for index, element in enumerate(elements):
                    element_base = base_offset + outer_stride * index
                    stores.extend(
                        parse_initializer(element, element_type, element_base),
                    )
                    used_bytes += outer_stride

                empty_cells = target_type.elements_count - present_count
                if empty_cells > 0:
                    total_bytes = target_type.size_in_bytes
                    free_bytes = total_bytes - used_bytes
                    if free_bytes > 0:
                        stores.append(
                            InitializerStorePlan(
                                offset=base_offset + used_bytes,
                                size=free_bytes,
                                kind="padding",
                            ),
                        )
                return tuple(stores)

            element_type = flat_target.element_type
            element_size = element_type.size_in_bytes
            total_count = flat_target.elements_count

            stores = []
            for index, element in enumerate(elements):
                element_offset = base_offset + element_size * index
                stores.extend(
                    parse_initializer(element, element_type, element_offset),
                )

            present_count = len(elements)
            if present_count < total_count:
                remaining_size = element_size * (total_count - present_count)
                remaining_offset = base_offset + element_size * present_count

                filler_value = 0
                has_filler = filler is not None
                if has_filler:
                    parsed_filler = _primitive_scalar_plan(filler, element_type)
                    if parsed_filler is not None and parsed_filler.kind == "int":
                        filler_value = (
                            parsed_filler.int_value
                            if parsed_filler.int_value is not None
                            else 0
                        )

                if filler_value == 0:
                    stores.append(
                        InitializerStorePlan(
                            offset=remaining_offset,
                            size=remaining_size,
                            kind="padding",
                        ),
                    )
                else:
                    stores.append(
                        InitializerStorePlan(
                            offset=remaining_offset,
                            size=element_size,
                            kind="fill",
                            fill_count=total_count - present_count,
                            fill_value=filler_value,
                        ),
                    )

            return tuple(stores)

        case (StructureLiteral(fields=fields), StructureType()):
            previous_taken = 0
            for field_name in target_type.order:
                if field_name not in fields:
                    continue
                field_type = target_type.get_field_type(field_name)
                field_offset = target_type.get_field_offset(field_name)
                padding = field_offset - previous_taken
                if padding > 0:
                    stores.append(
                        InitializerStorePlan(
                            offset=base_offset + previous_taken,
                            size=padding,
                            kind="padding",
                        ),
                    )
                field_stores = parse_initializer(
                    fields[field_name],
                    field_type,
                    base_offset + field_offset,
                )
                stores.extend(field_stores)
                previous_taken = field_offset + field_type.size_in_bytes

            trailing_padding = target_type.size_in_bytes - previous_taken
            if trailing_padding > 0:
                stores.append(
                    InitializerStorePlan(
                        offset=base_offset + previous_taken,
                        size=trailing_padding,
                        kind="padding",
                    ),
                )
            return tuple(stores)

    raise NotImplementedError((literal, target_type))


def _replace_offset(
    plan: InitializerStorePlan,
    base_offset: int,
) -> InitializerStorePlan:
    if base_offset == 0:
        return plan
    return InitializerStorePlan(
        offset=plan.offset + base_offset,
        size=plan.size,
        kind=plan.kind,
        int_value=plan.int_value,
        string_value=plan.string_value,
        fill_count=plan.fill_count,
        fill_value=plan.fill_value,
    )
