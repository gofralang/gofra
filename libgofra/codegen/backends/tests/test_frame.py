from itertools import pairwise
from pathlib import Path

from libgofra.codegen.backends.frame import build_local_variables_frame_offsets
from libgofra.hir.module import Module
from libgofra.hir.variable import Variable, VariableScopeClass, VariableStorageClass
from libgofra.lexer.tokens import TokenLocation
from libgofra.types.composite.array import ArrayType
from libgofra.types.primitive.character import CharType
from libgofra.types.primitive.integers import I64Type


def _local_var(name: str, type_: object) -> Variable:
    return Variable(
        name=name,
        module=Module(path=Path("test.gof")),
        defined_at=TokenLocation.toolchain(),
        is_constant=False,
        storage_class=VariableStorageClass.STACK,
        scope_class=VariableScopeClass.FUNCTION,
        type=type_,  # type: ignore[arg-type]
        initial_value=None,
    )


def _slot(offset: int, size_in_bytes: int) -> tuple[int, int]:
    """Return a slot of a local variable as a (bottom, top) frame-relative address range.

    A variable lives at `frame pointer - offset` and occupies memory upwards from that
    address, so its slot is `[offset - size, offset)` in the frame-relative coordinates.
    """
    return (offset - size_in_bytes, offset)


def _assert_slots_do_not_overlap(slots: list[tuple[int, int]]) -> None:
    for (_, top_a), (_, bottom_b) in pairwise(slots):
        assert top_a <= bottom_b, "local variable slots must not overlap"


def test_small_variables_do_not_overlap() -> None:
    variables = {
        "a": _local_var("a", I64Type()),
        "b": _local_var("b", I64Type()),
        "c": _local_var("c", I64Type()),
    }

    frame = build_local_variables_frame_offsets(variables)

    slots = [_slot(frame.offsets[name], 8) for name in ("a", "b", "c")]
    _assert_slots_do_not_overlap(slots)


def test_large_aggregate_does_not_overflow_frame() -> None:
    """A local variable bigger than its aligned slot must not grow out of the frame.

    Regression test: the slot of a variable is reserved *below* its base address, as the
    data of a variable grows upwards. Otherwise a big aggregate overwrites the saved
    frame pointer and the return address.
    """
    variables = {
        "small": _local_var("small", I64Type()),
        "big": _local_var("big", ArrayType(CharType(), 240)),
        "tail": _local_var("tail", I64Type()),
    }

    frame = build_local_variables_frame_offsets(variables)

    sizes = {"small": 8, "big": 240, "tail": 8}
    slots = {name: _slot(frame.offsets[name], sizes[name]) for name in variables}

    for name, (bottom, top) in slots.items():
        assert bottom >= 0, f"variable `{name}` must not grow below the frame"
        assert top <= frame.local_space_size, (
            f"variable `{name}` must not grow above the frame"
        )

    ordered = sorted(slots.values(), key=lambda slot: slot[1])
    _assert_slots_do_not_overlap(ordered)


def test_frame_size_is_not_affected_by_variables_order() -> None:
    variables = {
        "a": _local_var("a", I64Type()),
        "b": _local_var("b", ArrayType(CharType(), 128)),
    }

    frame = build_local_variables_frame_offsets(variables)

    # 8 bytes of the initial gap + 16 bytes (aligned int) + 128 bytes (aligned buffer)
    assert frame.local_space_size == 160
