"""Storage of the documents that are currently opened in the editor."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from gofra.lsp.positions import Position, position_to_index


@dataclass(frozen=True, slots=True)
class Document:
    """A source file that is opened in the editor."""

    uri: str
    path: Path
    text: str
    version: int

    @property
    def lines(self) -> list[str]:
        """Get the lines of the document (without line separators)."""
        return self.text.splitlines()

    def offset_at(self, position: Position) -> int:
        """Get the index of the given position inside the document text."""
        lines = self.text.splitlines(keepends=True)
        return position_to_index(position, lines)


@dataclass(slots=True)
class DocumentStore:
    """Keeps track of the documents that are opened in the editor."""

    _documents: dict[str, Document] = field(default_factory=dict)

    def open(self, uri: str, text: str, version: int) -> Document:
        """Register a newly opened document."""
        document = Document(
            uri=uri,
            path=uri_to_path(uri),
            text=text,
            version=version,
        )
        self._documents[uri] = document
        return document

    def change(self, uri: str, text: str, version: int) -> Document | None:
        """Apply a change of an already opened document."""
        existing = self._documents.get(uri)
        if existing is None:
            return None

        document = Document(
            uri=uri,
            path=existing.path,
            text=text,
            version=version,
        )
        self._documents[uri] = document
        return document

    def close(self, uri: str) -> None:
        """Forget a closed document."""
        self._documents.pop(uri, None)

    def get(self, uri: str) -> Document | None:
        """Get a document by its URI."""
        return self._documents.get(uri)

    def __contains__(self, uri: object) -> bool:
        """Check if a document with the given URI is opened."""
        return uri in self._documents


def uri_to_path(uri: str) -> Path:
    """Convert a file URI into a local filesystem path."""
    parsed = urlparse(uri)

    if parsed.scheme not in ("", "file"):
        return Path(uri)

    path = url2pathname(unquote(parsed.path))
    return Path(path)
