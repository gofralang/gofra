from pathlib import Path

from libgofra.hir.function import Function, FunctionParameter
from libgofra.hir.module import Module
from libgofra.hir.operator import Operator, OperatorType
from libgofra.hir.variable import Variable, VariableScopeClass, VariableStorageClass
from libgofra.lexer.tokens import Token, TokenLocation, TokenType
from libgofra.linter.context import LintContext
from libgofra.linter.diagnostics import LintLevel
from libgofra.linter.references import collect_references
from libgofra.linter.rules.unused_local_variable import UnusedLocalVariableRule
from libgofra.types.primitive.integers import I64Type
from libgofra.types.primitive.void import VoidType


def _loc() -> TokenLocation:
    return TokenLocation.toolchain()


def _local_var(name: str) -> Variable:
    return Variable(
        name=name,
        module=Module(path=Path("test.gof")),
        defined_at=_loc(),
        is_constant=False,
        storage_class=VariableStorageClass.STACK,
        scope_class=VariableScopeClass.FUNCTION,
        type=I64Type(),
        initial_value=None,
    )


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
    variables: dict[str, Variable] | None = None,
    parameters: list[FunctionParameter] | None = None,
    operators: list[Operator] | None = None,
) -> Function:
    return Function.create_internal(
        name=name,
        defined_at=_loc(),
        parameters=parameters or [],
        variables=variables or {},
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
        UnusedLocalVariableRule().check(
            module,
            LintContext(module=module, references=collect_references(module)),
        ),
    )


# --- fires ---


def test_fires_on_unused_local_variable() -> None:
    var = _local_var("x")
    fn = _make_function("f", variables={"x": var})
    module = _make_module(fn)

    diagnostics = _run(module)

    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.rule_id == "unused-local-variable"
    assert diag.level == LintLevel.WARN
    assert diag.at == var.defined_at
    assert "'x'" in diag.message


# --- skips ---


def test_skips_used_local_variable() -> None:
    fn = _make_function(
        "f",
        variables={"x": _local_var("x")},
        operators=[_push_var_value_op("x")],
    )
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


def test_skips_underscore_prefixed_local_variable() -> None:
    fn = _make_function("f", variables={"_ignored": _local_var("_ignored")})
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


def test_skips_parameters() -> None:
    # Parameters are materialized as local variables of the function scope,
    # but unused parameters are reported by the `unused-parameter` rule.
    param = _param("p")
    fn = _make_function(
        "f",
        variables={"p": _local_var("p")},
        parameters=[param],
    )
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
    fn.variables = {"x": _local_var("x")}
    module = _make_module(fn)

    diagnostics = _run(module)

    assert diagnostics == []


# --- mixed ---


def test_collects_only_unused_local_variables() -> None:
    used = _local_var("a")
    unused = _local_var("b")
    ignored = _local_var("_c")

    fn = _make_function(
        "f",
        variables={"a": used, "b": unused, "_c": ignored},
        operators=[_push_var_value_op("a")],
    )
    module = _make_module(fn)

    diagnostics = _run(module)

    assert len(diagnostics) == 1
    assert "'b'" in diagnostics[0].message
    assert "'a'" not in diagnostics[0].message
    assert "'_c'" not in diagnostics[0].message
