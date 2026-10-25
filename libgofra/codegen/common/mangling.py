import re

from libgofra.hir.function import Function
from libgofra.hir.variable import Variable
from libgofra.types import Type


def _sanitize_symbol_name(name: str) -> str:
    # C/assembly symbol names are intentionally conservative here.
    sanitized = re.sub(r"[^A-Za-z0-9_.]", "_", name)
    if not sanitized:
        sanitized = "_"
    if sanitized[0].isdigit():
        sanitized = f"_{sanitized}"
    return sanitized


def mangle_hir_symbol_name(symbol: Function | Variable[Type]) -> str:
    if isinstance(symbol, Function) and not symbol.attrs.mangle:
        return f"_{_sanitize_symbol_name(symbol.name)}"

    kind = "f" if isinstance(symbol, Function) else "g"
    mod = _sanitize_symbol_name(symbol.module.as_name)
    name = _sanitize_symbol_name(symbol.name)
    return f"_{mod}.{name}{kind}"
