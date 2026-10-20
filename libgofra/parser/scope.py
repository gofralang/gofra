from collections.abc import MutableMapping

from libgofra.hir.function import Function
from libgofra.hir.variable import Variable
from libgofra.types import Type
from libgofra.types.generics import GenericParametrizedType
from libgofra.types.registry import get_default_propagated_type_registry

type NameHolder = Function | Variable[Type] | GenericParametrizedType | Type


class Scope:
    parent: "Scope | None"
    functions: MutableMapping[str, Function]
    variables: MutableMapping[str, Variable]
    types: MutableMapping[str, Type | GenericParametrizedType]

    def __init__(self, parent: "Scope | None") -> None:
        self.parent = parent
        self.variables = {}
        self.functions = {}
        self.types = get_default_propagated_type_registry() if parent is None else {}

    def lookup(self, name: str) -> NameHolder | None:
        if (h := self._lookup_local(name)) is not None:
            return h
        return self.parent.lookup(name) if self.parent else None

    @property
    def is_global(self) -> bool:
        return self.parent is None

    def declare_function(self, function: Function) -> Function:
        assert function.name not in self.functions
        self.functions[function.name] = function

        return function

    def declare_type(
        self,
        name: str,
        type: Type | GenericParametrizedType,  # noqa: A002
    ) -> Type | GenericParametrizedType:
        assert name not in self.types
        self.types[name] = type
        return type

    def declare_variable(
        self,
        name: str,
        variable: Variable,
    ) -> Variable:
        assert name not in self.variables, name
        self.variables[name] = variable
        return variable

    def _lookup_local(self, name: str) -> NameHolder | None:
        if name in self.variables:
            return self.variables[name]
        if name in self.functions:
            return self.functions[name]
        if name in self.types:
            return self.types[name]
        return None
