from pathlib import Path

from libgofra.hir.function import Function
from libgofra.hir.module import Module
from libgofra.hir.operator import Operator, OperatorType
from libgofra.hir.variable import Variable, VariableScopeClass, VariableStorageClass
from libgofra.lexer.tokens import Token, TokenLocation, TokenType
from libgofra.linter.context import LintContext
from libgofra.linter.diagnostics import LintLevel
from libgofra.linter.references import collect_references
from libgofra.linter.rules.unused_global_variable import UnusedGlobalVariableRule
from libgofra.types.primitive.integers import I64Type
from libgofra.types.primitive.void import VoidType


def _loc() -> TokenLocation:
    return TokenLocation.toolchain()


def _global_var(name: str, *, is_constant: bool = False) -> Variable:
    return Variable(
        name=name,
        module=Module(path=Path("test.gof")),
        defined_at=_loc(),
        is_constant=is_constant,
        storage_class=VariableStorageClass.STATIC,
        scope_class=VariableScopeClass.GLOBAL,
        type=I64Type(),
        initial_value=None,
    )


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


def _make_function(name: str, operators: list[Operator]) -> Function:
    return Function.create_internal(
        name=name,
        defined_at=_loc(),
        parameters=[],
        variables={},
        operators=operators,
        return_type=VoidType(),
    )


def _make_module(
    *variables: Variable,
    functions: dict[str, Function] | None = None,
) -> Module:
    module = Module(path=Path("test.gof"))
    for v in variables:
        module.variables[v.name] = v
    for fn_name, fn in (functions or {}).items():
        fn.module = module
        module.functions[fn_name] = fn
    return module


def _run(module: Module):  # noqa: ANN202
    return list(
        UnusedGlobalVariableRule().check(
            module,
            LintContext(module=module, references=collect_references(module)),
        ),
    )


def test_fires_on_unused_global_variable() -> None:
    var = _global_var("g")
    module = _make_module(var)

    diagnostics = _run(module)

    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.rule_id == "unused-global-variable"
    assert diag.level == LintLevel.WARN
    assert diag.at == var.defined_at
    assert "g" in diag.message


def test_skips_used_global_variable() -> None:
    var = _global_var("g")
    fn = _make_function("main", [_push_var_value_op("g")])
    module = _make_module(var, functions={"main": fn})

    diagnostics = _run(module)

    assert diagnostics == []


def test_skips_constant_global_variable() -> None:
    var = _global_var("C", is_constant=True)
    module = _make_module(var)

    diagnostics = _run(module)

    assert diagnostics == []


def test_skips_underscore_prefixed_variable() -> None:
    var = _global_var("_ignored")
    module = _make_module(var)

    diagnostics = _run(module)

    assert diagnostics == []


def test_collects_only_unused_non_constant_variables() -> None:
    used = _global_var("used")
    unused = _global_var("unused")
    const = _global_var("CONST", is_constant=True)
    underscore = _global_var("_hidden")

    fn = _make_function("main", [_push_var_value_op("used")])
    module = _make_module(used, unused, const, underscore, functions={"main": fn})

    diagnostics = _run(module)

    assert len(diagnostics) == 1
    assert "unused" in diagnostics[0].message
