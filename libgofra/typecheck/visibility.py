from libgofra.hir.module import Module
from libgofra.hir.operator import FunctionCallOperand, OperatorType
from libgofra.parser.errors.private_symbol_access import PrivateSymbolAccessError
from libgofra.parser.exceptions import ParserUnknownFunctionError


def validate_function_existence_and_visibility(root: Module, module: Module) -> None:
    # TODO(@kirillzhosul): This must be refactored - as implemented new dependency system
    for func in module.executable_functions:
        for op in func.operators:
            if op.type == OperatorType.FUNCTION_CALL:
                assert isinstance(op.operand, FunctionCallOperand), op.operand
                resolved_symbol = module.resolve_function_dependency(
                    op.operand.module,
                    op.operand.get_name(),
                )
                if resolved_symbol is None:
                    print(f"[help] Tried to resolve import from {op.operand.module}")
                    raise ParserUnknownFunctionError(
                        at=op.token.location,
                        name=op.operand.get_name(),
                        functions_available=[],
                        best_match=None,
                    )
                if op.operand.module is not None:
                    func_owner_mod = module.dependencies[op.operand.module]
                    if (
                        not resolved_symbol.is_public
                        and func_owner_mod.path != root.path
                    ):
                        raise PrivateSymbolAccessError(
                            defined_at=resolved_symbol.defined_at,
                            symbol_name=resolved_symbol.name,
                            call_site=op.location,
                            target_module=op.operand.module,
                        )
                if resolved_symbol.attrs.inline:
                    msg = f"Call to inline function {resolved_symbol.name} (defined at {resolved_symbol.defined_at}) must be resolved inside parser level, but reached up to semantic stage - nor this call was not folded yet! Will emit linkage error (undefined reference to inline definition)"
                    raise ValueError(msg)
    for children_module in module.dependencies.values():
        validate_function_existence_and_visibility(root=root, module=children_module)
