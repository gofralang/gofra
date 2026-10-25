"""General string pool for codegen.

Provides general support for deduplication and tracking labels for unique strings.
"""

from collections.abc import ItemsView


class StringPool:
    """Deduplicating collection of codegen strings.

    Labels are unique within a pool and may be disambiguated with an optional
    scope. The scope is useful when several modules or compilation units are
    combined and local ``.strN`` labels would otherwise collide.
    """

    _next_id: int
    _scope: str | None
    _content_to_label: dict[str, str]

    def __init__(self, *, scope: str | None = None) -> None:
        self._content_to_label = {}
        self._next_id = 0
        self._scope = scope

    @staticmethod
    def _make_label(scope: str | None, identifier: int) -> str:
        label = f".str{identifier}"
        if scope:
            # Keep labels local-ish while making them unique across units.
            label = f".{scope}{label}"
        return label

    def add(self, raw_string: str) -> str:
        """Track a raw string and return its reusable codegen label."""
        label = self._content_to_label.get(raw_string)
        if label is not None:
            return label

        string_key = self._make_label(self._scope, self._next_id)
        self._next_id += 1
        self._content_to_label[raw_string] = string_key
        return string_key

    def is_empty(self) -> bool:
        """Return whether the pool has no tracked strings."""
        return not self._content_to_label

    def __len__(self) -> int:
        """Return number of unique tracked strings."""
        return len(self._content_to_label)

    def __contains__(self, raw_string: object) -> bool:
        """Return whether a raw string is already tracked."""
        return raw_string in self._content_to_label

    def items(self) -> ItemsView[str, str]:
        """Iterate over `(string, label)` pairs in insertion order."""
        return self._content_to_label.items()
