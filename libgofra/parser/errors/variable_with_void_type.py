from libgofra.exceptions import GofraError
from libgofra.lexer.tokens import TokenLocation
from libgofra.types.primitive.void import VoidType


class VariableCannotHasVoidTypeParserError(GofraError):
    def __init__(self, varname: str, defined_at: TokenLocation) -> None:
        self.varname = varname
        self.defined_at = defined_at

    def __repr__(self) -> str:
        return f"""Void type is prohibited for variable types!

Variable '{self.varname}' defined at {self.defined_at} has '{VoidType()}' type, which is prohibited!
Using this type makes size of variables zero, which means it cannot have any value/invariant and has no meaning!

[parser-variable-has-void-type]"""
