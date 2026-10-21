from pathlib import Path

from libgofra.hir.function import Function
from libgofra.hir.module import Module
from libgofra.hir.operator import Operator, OperatorType, TypecastMeta
from libgofra.lexer.tokens import Token, TokenLocation, TokenType
from libgofra.linter.context import LintContext
from libgofra.linter.diagnostics import LintLevel
from libgofra.linter.rules.redundant_typecast import RedundantTypecastRule
from libgofra.types.primitive.integers import I32Type, I64Type
from libgofra.types.primitive.void import VoidType


def _loc() -> TokenLocation:
    return TokenLocation.toolchain()


def _typecast_op(
    source: I64Type | I32Type,
    target: I64Type | I32Type,
) -> Operator:
    """Build a STATIC_TYPE_CAST operator with typechecker analysis metadata."""
    return Operator(
        type=OperatorType.STATIC_TYPE_CAST,
        token=Token(
            type=TokenType.KEYWORD,
            text="typecast",
            value="typecast",
            location=_loc(),
        ),
        operand=target,
        tc_meta=TypecastMeta(
            a=source,
            b=target,
            kind=TypecastMeta.Kind.REINTERPRET,
        ),
    )


def _make_function(
    name: str,
    operators: list[Operator] | None = None,
) -> Function:
    return Function.create_internal(
        name=name,
        defined_at=_loc(),
        parameters=[],
        variables={},
        operators=operators or [],
        return_type=VoidType(),
    )


def _make_module(*functions: Function) -> Module:
    module = Module(path=Path("test.gof"))
    for fn in functions:
        fn.module = module
        module.functions[fn.name] = fn
    return module


def _run(module: Module):  # noqa: ANN202
    return list(
        RedundantTypecastRule().check(
            module,
            LintContext(module=module),
        ),
    )


# --- fires ---


def test_fires_on_redundant_typecast() -> None:
    fn = _make_function("f", [_typecast_op(I64Type(), I64Type())])
    module = _make_module(fn)

    diagnostics = _run(module)

    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.rule_id == "redundant-typecast"
    assert diag.level == LintLevel.WARN
    assert diag.at == fn.defined_at
    assert "I64" in diag.message


# --- skips ---


def test_skips_cast_to_different_type() -> None:
    fn = _make_function("f", [_typecast_op(I64Type(), I32Type())])
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


def test_skips_function_without_typecasts() -> None:
    fn = _make_function("f", [])
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


def test_skips_typecast_without_typechecker_metadata() -> None:
    # Typechecker never reached this operator (e.g code after early return),
    # so there is no source type to compare against.
    operator = Operator(
        type=OperatorType.STATIC_TYPE_CAST,
        token=Token(
            type=TokenType.KEYWORD,
            text="typecast",
            value="typecast",
            location=_loc(),
        ),
        operand=I64Type(),
    )
    fn = _make_function("f", [operator])
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


def test_skips_external_function() -> None:
    fn = Function.create_external(
        name="ext",
        defined_at=_loc(),
        parameters=[],
        return_type=VoidType(),
    )
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


def test_skips_inline_function() -> None:
    fn = Function.create_internal_inline(
        name="inl",
        defined_at=_loc(),
        parameters=[],
        operators=[_typecast_op(I64Type(), I64Type())],
        return_type=VoidType(),
    )
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


# --- mixed ---


def test_collects_only_redundant_typecasts() -> None:
    redundant = _typecast_op(I64Type(), I64Type())
    narrowing = _typecast_op(I64Type(), I32Type())

    fn = _make_function("f", [redundant, narrowing])
    module = _make_module(fn)

    diagnostics = _run(module)

    assert len(diagnostics) == 1
    assert "I64" in diagnostics[0].message
    assert "I32" not in diagnostics[0].message
