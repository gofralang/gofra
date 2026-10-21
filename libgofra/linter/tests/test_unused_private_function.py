from pathlib import Path

from libgofra.hir.function import Function, Visibility
from libgofra.hir.module import Module
from libgofra.hir.operator import FunctionCallOperand, Operator, OperatorType
from libgofra.lexer.tokens import Token, TokenLocation, TokenType
from libgofra.linter.context import LintContext
from libgofra.linter.diagnostics import LintLevel
from libgofra.linter.rules.unused_private_function import UnusedPrivateFunctionRule
from libgofra.optimizer.helpers.call_graph import CallGraph
from libgofra.types.primitive.void import VoidType


def _loc() -> TokenLocation:
    return TokenLocation.toolchain()


def _call_op(name: str) -> Operator:
    return Operator(
        type=OperatorType.FUNCTION_CALL,
        token=Token(
            type=TokenType.IDENTIFIER,
            text=name,
            value=name,
            location=_loc(),
        ),
        operand=FunctionCallOperand(module=None, func=name),
    )


def _make_function(
    name: str,
    operators: list[Operator] | None = None,
    *,
    visibility: Visibility = Visibility.PRIVATE,
) -> Function:
    fn = Function.create_internal(
        name=name,
        defined_at=_loc(),
        parameters=[],
        variables={},
        operators=operators or [],
        return_type=VoidType(),
    )
    fn.attrs.visibility = visibility
    return fn


def _make_module(*functions: Function) -> Module:
    module = Module(path=Path("test.gof"))
    for fn in functions:
        fn.module = module
        module.functions[fn.name] = fn
    return module


def _run(module: Module):  # noqa: ANN202
    return list(
        UnusedPrivateFunctionRule().check(
            module,
            LintContext(module=module, call_graph=CallGraph(module)),
        ),
    )


# --- fires ---


def test_fires_on_unused_private_function() -> None:
    fn = _make_function("f")
    module = _make_module(fn)

    diagnostics = _run(module)

    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.rule_id == "unused-private-function"
    assert diag.level == LintLevel.WARN
    assert diag.at == fn.defined_at
    # Match the name as a whole -- a bare "f" would match any word containing
    # that letter (e.g. "function").
    assert "function f " in diag.message


# --- skips ---


def test_skips_called_private_function() -> None:
    callee = _make_function("callee")
    # The caller must be public, otherwise it is itself an unused private function
    # (nothing calls it) and is reported on its own.
    caller = _make_function(
        "caller",
        [_call_op("callee")],
        visibility=Visibility.PUBLIC,
    )
    module = _make_module(caller, callee)

    diagnostics = _run(module)

    assert diagnostics == []


def test_fires_on_private_function_that_calls_another() -> None:
    # A private function that is never called is reported on its own, even when
    # it calls something -- the callee is not reported as it has a caller.
    callee = _make_function("callee")
    caller = _make_function("caller", [_call_op("callee")])
    module = _make_module(caller, callee)

    diagnostics = _run(module)

    assert len(diagnostics) == 1
    assert "function caller " in diagnostics[0].message
    assert "function callee " not in diagnostics[0].message


def test_skips_public_function() -> None:
    fn = _make_function("f", visibility=Visibility.PUBLIC)
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
        operators=[],
        return_type=VoidType(),
    )
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


def test_skips_when_call_graph_is_absent() -> None:
    fn = _make_function("f")
    module = _make_module(fn)

    diagnostics = list(
        UnusedPrivateFunctionRule().check(
            module,
            LintContext(module=module),
        ),
    )

    assert diagnostics == []


# --- mixed ---


def test_collects_only_unused_private_functions() -> None:
    unused = _make_function("unused")
    public = _make_function("public", visibility=Visibility.PUBLIC)
    called = _make_function("called")
    caller = _make_function(
        "caller",
        [_call_op("called")],
        visibility=Visibility.PUBLIC,
    )

    module = _make_module(unused, public, called, caller)

    diagnostics = _run(module)

    assert len(diagnostics) == 1
    assert "function unused " in diagnostics[0].message
    assert "function public " not in diagnostics[0].message
    assert "function called " not in diagnostics[0].message
    assert "function caller " not in diagnostics[0].message
