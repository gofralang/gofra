from pathlib import Path

from libgofra.hir.function import Function, FunctionParameter
from libgofra.hir.module import Module
from libgofra.hir.operator import Operator, OperatorType
from libgofra.lexer.tokens import Token, TokenLocation, TokenType
from libgofra.linter.context import LintContext
from libgofra.linter.diagnostics import LintLevel
from libgofra.linter.references import collect_references
from libgofra.linter.rules.unused_parameter import UnusedParameterRule
from libgofra.types.primitive.integers import I64Type
from libgofra.types.primitive.void import VoidType


def _loc() -> TokenLocation:
    return TokenLocation.toolchain()


def _param(name: str) -> FunctionParameter:
    return FunctionParameter(name=name, type=I64Type())


def _push_var_value_op(name: str) -> Operator:
    return Operator(
        type=OperatorType.PUSH_VARIABLE_VALUE,
        token=Token(
            type=TokenType.IDENTIFIER,
            text=name,
            value=name,
            location=_loc(),
        ),
        operand=name,
    )


def _make_function(
    name: str,
    params: list[FunctionParameter],
    operators: list[Operator] | None = None,
) -> Function:
    return Function.create_internal(
        name=name,
        defined_at=_loc(),
        parameters=params,
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
        UnusedParameterRule().check(
            module,
            LintContext(module=module, references=collect_references(module)),
        ),
    )


# --- fires ---


def test_fires_on_unused_parameter() -> None:
    fn = _make_function("f", [_param("x")], operators=[])
    module = _make_module(fn)

    diagnostics = _run(module)

    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.rule_id == "unused-parameter"
    assert diag.level == LintLevel.WARN
    assert diag.at == fn.defined_at
    assert "x" in diag.message
    assert "f" in diag.message


# --- skips ---


def test_skips_used_parameter() -> None:
    fn = _make_function(
        "f",
        [_param("x")],
        operators=[_push_var_value_op("x")],
    )
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


def test_skips_underscore_prefixed_parameter() -> None:
    fn = _make_function("f", [_param("_ignored")], operators=[])
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


def test_skips_external_function() -> None:
    fn = Function.create_external(
        name="ext",
        defined_at=_loc(),
        parameters=[_param("x")],
        return_type=VoidType(),
    )
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


def test_skips_inline_function() -> None:
    fn = Function.create_internal_inline(
        name="inl",
        defined_at=_loc(),
        parameters=[_param("x")],
        operators=[],
        return_type=VoidType(),
    )
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


# --- mixed ---


def test_collects_only_unused_used_non_underscore() -> None:
    used = _param("a")
    unused = _param("b")
    ignored = _param("_c")

    fn = _make_function(
        "f",
        [used, unused, ignored],
        operators=[_push_var_value_op("a")],
    )
    module = _make_module(fn)

    diagnostics = _run(module)

    assert len(diagnostics) == 1
    # Names are backtick-quoted in the message, so compare them as a whole --
    # a bare "a" would match any word containing that letter (e.g. "parameter").
    assert "`b`" in diagnostics[0].message
    assert "`a`" not in diagnostics[0].message
    assert "`_c`" not in diagnostics[0].message
