from collections.abc import Mapping
from typing import NamedTuple

from libgofra.codegen.backends.alignment import align_to_highest_size
from libgofra.codegen.backends.errors import FrameTableLocatableError
from libgofra.codegen.config import CodegenConfig
from libgofra.hir.function import Function
from libgofra.hir.variable import Variable
from libgofra.types._base import Type

# Size of frame head (FP, LR registers)
FRAME_HEAD_SIZE = 8 * 2

STORE_PAIR_MAX_RANGE = 2**12 - 1


class LocalVariablesFrameOffsets(NamedTuple):
    """Offsets within frame for local variables."""

    offsets: Mapping[str, int]
    local_space_size: int


def build_local_variables_frame_offsets(
    variables: Mapping[str, Variable[Type]],
    *,
    initial_offset: int = 8,
) -> LocalVariablesFrameOffsets:
    """Construct mapping from local variable name to stack frame offset where that variable should live.

    We allocate some space under stack/frame pointer for local variables (beside FP and LR itself).
    And we need convenient mapping for accessing local variables allocated at that space.

    Offsets are counted downwards from the frame pointer, as the variable is located at
    `frame pointer - offset` (e.g `X29 - offset` on AARCH64, `RBP - offset` on AMD64).

    A variable occupies memory upwards from its base address, therefore the space for a variable
    must be reserved *below* that base address. That is why the offset is incremented by the
    (aligned) size of the variable *before* the offset is assigned - otherwise a variable which
    is bigger than its aligned slot would grow out of the frame and overwrite the saved
    frame pointer and return address.

    That function constructs something like:
    {
        'var1': 16, # +16 bytes from frame
        'var2': 32 # +32 bytes from frame
        ...
    }

    Total offsets must be aligned to 16 bytes on AARCH64, so sum of these variables is not 24, but 32 bytes (space may be used or leftover for alignment)

    So looking at the frame with alignment:
    [SP]
    [SP - 8]:  FP
    [SP - 16]: LR
    """
    offsets: dict[str, int] = {}
    current_offset = initial_offset

    for var_name, var in variables.items():
        # Reserve the slot for the variable below its base address (as the data grows upwards)
        current_offset += align_to_highest_size(var.size_in_bytes)
        offsets[var_name] = current_offset

    # Alignment is required on AARCH64
    local_space_size = align_to_highest_size(current_offset)

    if local_space_size > STORE_PAIR_MAX_RANGE:
        # TODO(@kirillzhosul): rework this error
        raise FrameTableLocatableError(local_space_size, STORE_PAIR_MAX_RANGE)

    return LocalVariablesFrameOffsets(
        offsets=offsets,
        local_space_size=local_space_size,
    )


def is_native_function_has_frame(config: CodegenConfig, function: Function) -> bool:
    """Return is this function must define frame pointer in codegen."""
    if function.attrs.inline:
        return True  # TODO(@kirillzhosul): research while inline functions depend on frame?

    if function.attrs.naked:  # Naked has no frame by its definition
        return False

    if function.variables:  # Must hold frame due to variables located on the frame
        return True

    if not function.attrs.leaf:  # If has any calls we cant skip frame setup
        return True

    return not config.omit_unused_frame_pointers
