from libgofra.hir.function import Function
from libgofra.hir.variable import Variable
from libgofra.types import Type


def mangle_hir_symbol_name(symbol: Function | Variable[Type]) -> str:
    if isinstance(symbol, Function) and not symbol.attrs.mangle:
        return f"_{symbol.name}"

    kind = "f" if isinstance(symbol, Function) else "g"
    mod = symbol.module.as_name
    name = symbol.name
    return f"_{mod}.{name}{kind}"
