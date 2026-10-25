from libgofra.hir.function import Function
from libgofra.parser.exceptions import ParserEntryPointFunctionModifiersError
from libgofra.typecheck.errors.entry_point_parameters_mismatch import (
    EntryPointParametersMismatchTypecheckError,
)
from libgofra.typecheck.errors.entry_point_return_type_mismatch import (
    EntryPointReturnTypeMismatchTypecheckError,
)
from libgofra.types.composite.pointer import PointerType
from libgofra.types.primitive.integers import I64Type


def validate_entry_point_signature(entry_point: Function) -> None:
    # TODO(@kirillzhosul): these parser errors comes from legacy entry point validation, must be reworked later - https://github.com/kirillzhosul/gofra/issues/28

    if entry_point.attrs.external or entry_point.attrs.inline:
        raise ParserEntryPointFunctionModifiersError(entry_point_name=entry_point.name)

    retval_t = entry_point.return_type
    if entry_point.has_return_value() and not isinstance(retval_t, I64Type):
        raise EntryPointReturnTypeMismatchTypecheckError(
            return_type=retval_t,
            entry_point_name=entry_point.name,
        )

    parameters = entry_point.parameters
    if len(parameters) == 0:
        pass
    elif len(parameters) == 2:
        if not isinstance(parameters[0].type, I64Type) or not isinstance(
            parameters[1].type,
            PointerType,
        ):
            raise EntryPointParametersMismatchTypecheckError(
                parameters=entry_point.parameter_types,
                entry_point_name=entry_point.name,
            )
    else:
        raise EntryPointParametersMismatchTypecheckError(
            parameters=entry_point.parameter_types,
            entry_point_name=entry_point.name,
        )
