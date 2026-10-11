from collections.abc import Mapping

from libgofra.types._base import CompositeType, Type


class UnionType(CompositeType):
    """Type that holds fields as their representation as structure (sum type)."""

    members: Mapping[str, Type]

    name: str
    size_in_bytes: int

    def __init__(
        self,
        name: str,
        members: Mapping[str, Type],
    ) -> None:
        self.name = name

        self.members = members
        self._rebuild()

    def __repr__(self) -> str:
        return f"Union {self.name}"

    def _rebuild(self) -> None:
        self.size_in_bytes = (
            max(s.size_in_bytes for s in self.members.values()) if self.members else 0
        )

    def backpatch(
        self,
        members: Mapping[str, Type],
    ) -> None:
        """Backpatch union with new fields.

        Required when building an union as *reference* (e.g non-immediate union parsing)
        """
        self.members = members
        self._rebuild()

    def get_member_type(self, member_name: str) -> Type:
        """Get underlying type of member by name."""
        assert member_name in self.members
        return self.members[member_name]

    def has_member(self, member_name: str) -> bool:
        """Is union has this member?."""
        return member_name in self.members
