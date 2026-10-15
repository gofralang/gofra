from libgofra.types import Type
from libgofra.types.composite.array import ArrayType
from libgofra.types.composite.pointer import PointerMemoryLocation, PointerType
from libgofra.types.composite.structure import StructureType
from libgofra.types.primitive.integers import I64Type


class SliceType(StructureType):
    """Type that holds array as an view (slice) of ArrayType."""

    element_type: Type

    def __init__(
        self,
        element_type: Type,
        *,
        pma: PointerMemoryLocation | None = None,
    ) -> None:

        self.element_type = element_type

        data = PointerType(
            ArrayType(element_type=element_type, elements_count=0),
            memory_location=pma,
        )

        super().__init__(
            name="Slice",
            fields={
                "data": data,
                "len": I64Type(),
            },
            order=["data", "len"],
            is_packed=True,
            reorder=False,
        )

    def as_raw_array(self) -> ArrayType:
        return ArrayType(element_type=self.element_type, elements_count=0)

    def __repr__(self) -> str:
        return f"[]{self.element_type}"
