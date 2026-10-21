from pathlib import Path

from libgofra.hir.function import Function
from libgofra.hir.module import Module
from libgofra.hir.operator import Operator, OperatorType
from libgofra.lexer.tokens import Token, TokenLocation, TokenType
from libgofra.linter.context import LintContext
from libgofra.linter.diagnostics import LintLevel
from libgofra.linter.rules.empty_function_body import EmptyFunctionBodyRule
from libgofra.types.primitive.void import VoidType


def _loc() -> TokenLocation:
    return TokenLocation.toolchain()


def _dummy_operator() -> Operator:
    return Operator(
        type=OperatorType.STACK_DROP,
        token=Token(
            type=TokenType.KEYWORD,
            text="drop",
            value="drop",
            location=_loc(),
        ),
        operand=None,
    )


def _make_internal_function(
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


def _make_external_function(name: str) -> Function:
    return Function.create_external(
        name=name,
        defined_at=_loc(),
        parameters=[],
        return_type=VoidType(),
    )


def _make_inline_function(
    name: str,
    operators: list[Operator] | None = None,
) -> Function:
    return Function.create_internal_inline(
        name=name,
        defined_at=_loc(),
        parameters=[],
        operators=operators or [],
        return_type=VoidType(),
    )


def _make_module(*functions: Function) -> Module:
    module = Module(path=Path("test.gof"))
    for fn in functions:
        fn.module = module
        module.functions[fn.name] = fn
    return module


def test_fires_on_internal_function_with_empty_body() -> None:
    fn = _make_internal_function("empty")
    module = _make_module(fn)

    rule = EmptyFunctionBodyRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.rule_id == "empty-function-body"
    assert diag.level == LintLevel.WARN
    assert diag.at == fn.defined_at
    assert "empty" in diag.message
    assert "no executable body" in diag.message


def test_skips_internal_function_with_body() -> None:
    fn = _make_internal_function("ok", [_dummy_operator()])
    module = _make_module(fn)

    rule = EmptyFunctionBodyRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []


def test_skips_external_function() -> None:
    fn = _make_external_function("ext")
    module = _make_module(fn)

    rule = EmptyFunctionBodyRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []


def test_skips_inline_function() -> None:
    # inline functions have no own body — expanded at call site, not warned
    fn = _make_inline_function("inl")
    module = _make_module(fn)

    rule = EmptyFunctionBodyRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []


def test_collects_only_empty_internal_functions() -> None:
    ok_fn = _make_internal_function("ok", [_dummy_operator()])
    empty_fn = _make_internal_function("empty")
    external_fn = _make_external_function("ext")
    inline_fn = _make_inline_function("inl")

    module = _make_module(ok_fn, empty_fn, external_fn, inline_fn)

    rule = EmptyFunctionBodyRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert len(diagnostics) == 1
    # Names are backtick-quoted in the message, so compare them as a whole --
    # a bare "ok" would match any word containing that letter (e.g. "block").
    assert "`empty`" in diagnostics[0].message
    assert "`ok`" not in diagnostics[0].message
    assert "`ext`" not in diagnostics[0].message
    assert "`inl`" not in diagnostics[0].message
