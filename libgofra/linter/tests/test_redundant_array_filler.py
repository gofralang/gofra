from pathlib import Path

from libgofra.hir.function import Function
from libgofra.hir.literals import ArrayLiteral, IntegerLiteral, Literal_T
from libgofra.hir.module import Module
from libgofra.hir.variable import Variable, VariableScopeClass, VariableStorageClass
from libgofra.lexer.tokens import Token, TokenLocation, TokenType
from libgofra.linter.context import LintContext
from libgofra.linter.diagnostics import LintLevel
from libgofra.linter.rules.redundant_array_filler import RedundantArrayFillerRule
from libgofra.types.composite.array import ArrayType
from libgofra.types.primitive.integers import I64Type
from libgofra.types.primitive.void import VoidType


def _loc() -> TokenLocation:
    return TokenLocation.toolchain()


def _int_lit(value: int) -> IntegerLiteral:
    return IntegerLiteral(
        token=Token(
            type=TokenType.INTEGER,
            text=str(value),
            value=value,
            location=_loc(),
        ),
        value=value,
    )


def _array_lit(elements: list[Literal_T], default: Literal_T | None) -> ArrayLiteral:
    return ArrayLiteral(
        token=Token(type=TokenType.LBRACKET, text="[", value="", location=_loc()),
        elements=elements,
        default=default,
    )


def _make_array_var(  # noqa: PLR0913
    name: str,
    array_size: int,
    elements: list[Literal_T],
    filler: Literal_T | None,
    *,
    scope_class: VariableScopeClass = VariableScopeClass.GLOBAL,
    storage_class: VariableStorageClass = VariableStorageClass.STATIC,
    module: Module | None = None,
) -> Variable:
    return Variable(
        name=name,
        module=module or Module(path=Path("test.gof")),
        defined_at=_loc(),
        is_constant=False,
        storage_class=storage_class,
        scope_class=scope_class,
        type=ArrayType(element_type=I64Type(), elements_count=array_size),
        initial_value=_array_lit(elements, filler),
    )


def _make_function(name: str, variables: dict[str, Variable]) -> Function:
    return Function.create_internal(
        name=name,
        defined_at=_loc(),
        parameters=[],
        variables=variables,
        operators=[],
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


def test_fires_on_global_fully_populated_array_with_filler() -> None:
    var = _make_array_var(
        "a",
        3,
        [_int_lit(1), _int_lit(2), _int_lit(3)],
        _int_lit(0),
    )
    module = _make_module(var)
    rule = RedundantArrayFillerRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.rule_id == "redundant-array-filler"
    assert diag.level == LintLevel.WARN
    assert diag.at == var.defined_at
    assert "3/3" in diag.message


def test_skips_global_array_with_unused_filler_when_not_full() -> None:
    var = _make_array_var(
        "a",
        5,
        [_int_lit(1), _int_lit(2), _int_lit(3)],
        _int_lit(0),
    )
    module = _make_module(var)
    rule = RedundantArrayFillerRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []


def test_skips_global_array_without_filler() -> None:
    var = _make_array_var(
        "a",
        3,
        [_int_lit(1), _int_lit(2), _int_lit(3)],
        None,
    )
    module = _make_module(var)
    rule = RedundantArrayFillerRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []


# --- local variables ---


def test_fires_on_local_fully_populated_array_with_filler() -> None:
    local_var = _make_array_var(
        "x",
        2,
        [_int_lit(10), _int_lit(20)],
        _int_lit(0),
        scope_class=VariableScopeClass.FUNCTION,
        storage_class=VariableStorageClass.STACK,
    )
    fn = _make_function("main", {"x": local_var})
    module = _make_module(functions={"main": fn})

    rule = RedundantArrayFillerRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.rule_id == "redundant-array-filler"
    assert "x" in diag.message
    assert diag.at == local_var.defined_at


def test_skips_local_array_without_filler() -> None:
    local_var = _make_array_var(
        "x",
        2,
        [_int_lit(10), _int_lit(20)],
        None,
        scope_class=VariableScopeClass.FUNCTION,
        storage_class=VariableStorageClass.STACK,
    )
    fn = _make_function("main", {"x": local_var})
    module = _make_module(functions={"main": fn})

    rule = RedundantArrayFillerRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []


def test_skips_local_array_with_unused_filler_when_not_full() -> None:
    local_var = _make_array_var(
        "x",
        5,
        [_int_lit(1), _int_lit(2)],
        _int_lit(0),
        scope_class=VariableScopeClass.FUNCTION,
        storage_class=VariableStorageClass.STACK,
    )
    fn = _make_function("main", {"x": local_var})
    module = _make_module(functions={"main": fn})

    rule = RedundantArrayFillerRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []


# --- both scopes ---


def test_collects_from_both_global_and_local_variables() -> None:
    global_var = _make_array_var(
        "g",
        2,
        [_int_lit(1), _int_lit(2)],
        _int_lit(0),
    )
    local_var = _make_array_var(
        "l",
        3,
        [_int_lit(1), _int_lit(2), _int_lit(3)],
        _int_lit(0),
        scope_class=VariableScopeClass.FUNCTION,
        storage_class=VariableStorageClass.STACK,
    )
    fn = _make_function("main", {"l": local_var})
    module = _make_module(global_var, functions={"main": fn})

    rule = RedundantArrayFillerRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert len(diagnostics) == 2
    names = {d.message.split("`")[1] for d in diagnostics}
    assert names == {"g", "l"}


def test_skips_non_array_variable() -> None:
    module = Module(path=Path("test.gof"))
    var = Variable(
        name="x",
        module=module,
        defined_at=_loc(),
        is_constant=False,
        storage_class=VariableStorageClass.STATIC,
        scope_class=VariableScopeClass.GLOBAL,
        type=I64Type(),
        initial_value=_int_lit(5),
    )
    module.variables["x"] = var

    rule = RedundantArrayFillerRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []


def test_skips_non_array_literal_initializer() -> None:
    module = Module(path=Path("test.gof"))
    var = Variable(
        name="a",
        module=module,
        defined_at=_loc(),
        is_constant=False,
        storage_class=VariableStorageClass.STATIC,
        scope_class=VariableScopeClass.GLOBAL,
        type=ArrayType(element_type=I64Type(), elements_count=3),
        initial_value=_int_lit(5),
    )
    module.variables["a"] = var

    rule = RedundantArrayFillerRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []


def test_skips_external_function_variables() -> None:
    external_fn = Function.create_external(
        name="ext",
        defined_at=_loc(),
        parameters=[],
        return_type=VoidType(),
    )
    module = Module(path=Path("test.gof"))
    module.functions["ext"] = external_fn

    rule = RedundantArrayFillerRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert diagnostics == []


def test_multidimensional_uses_outer_elements_count() -> None:
    # int[2][3] = [[1,2,3], [4,5,6]; [0,0,0]]
    # Outer: 2/2 populated -> filler is redundant at outer level
    inner_type = ArrayType(element_type=I64Type(), elements_count=3)
    outer_type = ArrayType(element_type=inner_type, elements_count=2)

    inner1 = _array_lit([_int_lit(1), _int_lit(2), _int_lit(3)], None)
    inner2 = _array_lit([_int_lit(4), _int_lit(5), _int_lit(6)], None)
    outer_filler = _array_lit([_int_lit(0), _int_lit(0), _int_lit(0)], None)

    module = Module(path=Path("test.gof"))
    var = Variable(
        name="m",
        module=module,
        defined_at=_loc(),
        is_constant=False,
        storage_class=VariableStorageClass.STATIC,
        scope_class=VariableScopeClass.GLOBAL,
        type=outer_type,
        initial_value=_array_lit([inner1, inner2], outer_filler),
    )
    module.variables["m"] = var

    rule = RedundantArrayFillerRule()
    diagnostics = list(rule.check(module, LintContext(module=module)))

    assert len(diagnostics) == 1
    assert "2/2" in diagnostics[0].message
