from pathlib import Path

from libgofra.hir.module import Module
from libgofra.linter.context import LintContext
from libgofra.linter.diagnostics import LintLevel
from libgofra.linter.rules.struct_reorder_hint import StructReorderHintRule
from libgofra.types.composite.structure import StructureType
from libgofra.types.primitive.character import CharType
from libgofra.types.primitive.integers import I64Type


def _make_module(*structs: StructureType) -> Module:
    module = Module(path=Path("test.gof"))
    for s in structs:
        module.types[s.name] = s
    return module


def _make_struct(
    name: str,
    fields: dict,
    order: list[str],
    *,
    packed: bool = False,
    reorder: bool = False,
) -> StructureType:
    return StructureType(
        name=name,
        fields=fields,
        order=order,
        is_packed=packed,
        reorder=reorder,
    )


def test_reorder_hint_fires_on_wasteful_layout() -> None:
    # char (1) + i64 (8) + char (1) -> 24 bytes with padding (8 + 8 + 8)
    # reordered: i64 + char + char -> 16 bytes (8 + 1 + 1 + 6 padding)
    struct = _make_struct(
        "Wasteful",
        fields={"c1": CharType(), "i": I64Type(), "c2": CharType()},
        order=["c1", "i", "c2"],
    )
    module = _make_module(struct)
    rule = StructReorderHintRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.rule_id == "struct-reorder-hint"
    assert diag.level == LintLevel.WARN
    assert "Wasteful" in diag.message


def test_reorder_hint_skips_optimal_layout() -> None:
    # i64 + char + char -> already optimal (16 bytes)
    struct = _make_struct(
        "Optimal",
        fields={"i": I64Type(), "c1": CharType(), "c2": CharType()},
        order=["i", "c1", "c2"],
    )
    module = _make_module(struct)
    rule = StructReorderHintRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []


def test_reorder_hint_skips_packed() -> None:
    struct = _make_struct(
        "Packed",
        fields={"c1": CharType(), "i": I64Type(), "c2": CharType()},
        order=["c1", "i", "c2"],
        packed=True,
    )
    module = _make_module(struct)
    rule = StructReorderHintRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []


def test_reorder_hint_skips_already_reorder() -> None:
    struct = _make_struct(
        "AlreadyReordered",
        fields={"c1": CharType(), "i": I64Type(), "c2": CharType()},
        order=["i", "c1", "c2"],
        reorder=True,
    )
    module = _make_module(struct)
    rule = StructReorderHintRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []
