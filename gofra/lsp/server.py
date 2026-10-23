"""The Gofra language server."""

from __future__ import annotations

import sys
from typing import IO, Final

from gofra.lsp.analysis import Analysis, analyze_document
from gofra.lsp.documents import Document, DocumentStore
from gofra.lsp.features.completion import completion
from gofra.lsp.features.definition import definition
from gofra.lsp.features.hover import hover
from gofra.lsp.features.symbols import document_symbols
from gofra.lsp.positions import Position
from gofra.lsp.protocol import (
    ERROR_CODE_METHOD_NOT_FOUND,
    make_error_response,
    make_notification,
    make_response,
    read_message,
    write_message,
)
from libgofra import __version__

#: Name of the server that is reported to the client.
SERVER_NAME: Final = "gofra-lsp"

#: Text document sync kind that asks the client to send the whole document.
TEXT_DOCUMENT_SYNC_FULL: Final = 1


class LspServer:
    """Serves the Gofra language features over the Language Server Protocol."""

    def __init__(self, stdin: IO[bytes], stdout: IO[bytes]) -> None:
        self._stdin = stdin
        self._stdout = stdout
        self._documents = DocumentStore()
        self._analyses: dict[str, Analysis] = {}

    def run(self) -> int:
        """Serve the requests until the client closes the connection."""
        while True:
            message = read_message(self._stdin)
            if message is None:
                break

            if not self._handle(message):
                break

        return 0

    def _handle(self, message: dict[str, object]) -> bool:
        """Handle a single incoming message.

        :returns: False if the server must stop.
        """
        method = message.get("method")
        if not isinstance(method, str):
            return True

        params = message.get("params")
        if not isinstance(params, dict):
            params = {}

        request_id = message.get("id")

        if method == "initialize":
            self._respond(request_id, self._initialize())
        elif method == "initialized":
            pass
        elif method == "shutdown":
            self._respond(request_id, None)
        elif method == "exit":
            return False
        elif method == "textDocument/didOpen":
            self._did_open(params)
        elif method == "textDocument/didChange":
            self._did_change(params)
        elif method == "textDocument/didClose":
            self._did_close(params)
        elif method == "textDocument/didSave":
            self._did_save(params)
        elif method == "textDocument/documentSymbol":
            self._respond(request_id, self._document_symbol(params))
        elif method == "textDocument/hover":
            self._respond(request_id, self._hover(params))
        elif method == "textDocument/definition":
            self._respond(request_id, self._definition(params))
        elif method == "textDocument/completion":
            self._respond(request_id, self._completion(params))
        elif request_id is not None:
            self._error(
                request_id,
                ERROR_CODE_METHOD_NOT_FOUND,
                f"Method not found: {method}",
            )

        return True

    def _initialize(self) -> dict[str, object]:
        """Build the response of the initialize request."""
        return {
            "capabilities": {
                "positionEncoding": "utf-16",
                "textDocumentSync": {
                    "openClose": True,
                    "change": TEXT_DOCUMENT_SYNC_FULL,
                    "save": {"includeText": False},
                },
                "documentSymbolProvider": True,
                "hoverProvider": True,
                "definitionProvider": True,
                "completionProvider": {
                    "resolveProvider": False,
                    "triggerCharacters": ["."],
                },
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": __version__,
            },
        }

    def _did_open(self, params: dict[str, object]) -> None:
        """Handle the opening of a document."""
        text_document = params.get("textDocument")
        if not isinstance(text_document, dict):
            return

        uri = text_document.get("uri")
        text = text_document.get("text")
        version = text_document.get("version")
        if not isinstance(uri, str) or not isinstance(text, str):
            return

        self._documents.open(
            uri,
            text,
            version if isinstance(version, int) else 0,
        )
        self._analyze(uri)

    def _did_change(self, params: dict[str, object]) -> None:
        """Handle a change of an opened document."""
        text_document = params.get("textDocument")
        if not isinstance(text_document, dict):
            return

        uri = text_document.get("uri")
        version = text_document.get("version")
        if not isinstance(uri, str):
            return

        changes = params.get("contentChanges")
        if not isinstance(changes, list):
            return

        text = self._documents.get(uri).text if uri in self._documents else None
        for change in changes:
            if not isinstance(change, dict):
                continue
            new_text = change.get("text")
            if isinstance(new_text, str):
                text = new_text

        if text is None:
            return

        self._documents.change(
            uri,
            text,
            version if isinstance(version, int) else 0,
        )
        self._analyze(uri)

    def _did_close(self, params: dict[str, object]) -> None:
        """Handle the closing of a document."""
        text_document = params.get("textDocument")
        if not isinstance(text_document, dict):
            return

        uri = text_document.get("uri")
        if not isinstance(uri, str):
            return

        self._documents.close(uri)
        self._analyses.pop(uri, None)
        self._publish(uri, [])

    def _did_save(self, params: dict[str, object]) -> None:
        """Handle the saving of a document."""
        text_document = params.get("textDocument")
        if not isinstance(text_document, dict):
            return

        uri = text_document.get("uri")
        if not isinstance(uri, str):
            return

        self._analyze(uri)

    def _analyze(self, uri: str) -> None:
        """Analyze the document and publish the found problems."""
        document = self._documents.get(uri)
        if document is None:
            return

        try:
            analysis = analyze_document(document)
        except Exception as error:  # noqa: BLE001
            self._publish(
                uri,
                [
                    {
                        "range": {
                            "start": {"line": 0, "character": 0},
                            "end": {"line": 0, "character": 0},
                        },
                        "severity": 1,
                        "source": "gofra",
                        "message": f"Internal error: {error}",
                    },
                ],
            )
            return

        self._analyses[uri] = analysis
        self._publish(
            uri,
            [diagnostic.to_lsp() for diagnostic in analysis.diagnostics],
        )

    def _publish(self, uri: str, diagnostics: list[dict[str, object]]) -> None:
        """Send the diagnostics of a document to the client."""
        self._send(
            make_notification(
                "textDocument/publishDiagnostics",
                {"uri": uri, "diagnostics": diagnostics},
            ),
        )

    def _document_symbol(self, params: dict[str, object]) -> list[dict[str, object]]:
        """Get the symbols of a document."""
        document, analysis = self._document_with_analysis(params)
        if document is None or analysis is None or analysis.module is None:
            return []

        return document_symbols(analysis.module, document)

    def _hover(self, params: dict[str, object]) -> dict[str, object] | None:
        """Get the hover information of a document."""
        document, analysis = self._document_with_analysis(params)
        if document is None or analysis is None or analysis.module is None:
            return None

        position = _position_of(params)
        if position is None:
            return None

        return hover(analysis.module, document, position)

    def _definition(self, params: dict[str, object]) -> list[dict[str, object]] | None:
        """Get the definition location of a symbol."""
        document, analysis = self._document_with_analysis(params)
        if document is None or analysis is None or analysis.module is None:
            return None

        position = _position_of(params)
        if position is None:
            return None

        return definition(analysis.module, document, position)

    def _completion(self, params: dict[str, object]) -> list[dict[str, object]]:
        """Get the completion items of a document."""
        document, analysis = self._document_with_analysis(params)
        if document is None or analysis is None or analysis.module is None:
            return []

        position = _position_of(params)
        if position is None:
            return []

        return completion(analysis.module, document, position)

    def _document_with_analysis(
        self,
        params: dict[str, object],
    ) -> tuple[Document | None, Analysis | None]:
        """Get the document and its analysis by the request parameters."""
        text_document = params.get("textDocument")
        if not isinstance(text_document, dict):
            return None, None

        uri = text_document.get("uri")
        if not isinstance(uri, str):
            return None, None

        return self._documents.get(uri), self._analyses.get(uri)

    def _respond(self, request_id: object, result: object) -> None:
        """Send a response to the client."""
        if request_id is None:
            return

        self._send(make_response(request_id, result))

    def _error(self, request_id: object, code: int, message: str) -> None:
        """Send an error response to the client."""
        if request_id is None:
            return

        self._send(make_error_response(request_id, code, message))

    def _send(self, payload: dict[str, object]) -> None:
        """Send a message to the client."""
        write_message(self._stdout, payload)


def _position_of(params: dict[str, object]) -> Position | None:
    """Get the position of a request parameters."""
    position = params.get("position")
    if not isinstance(position, dict):
        return None

    line = position.get("line")
    character = position.get("character")
    if not isinstance(line, int) or not isinstance(character, int):
        return None

    return Position(line=line, character=character)


def serve(stdin: IO[bytes] | None = None, stdout: IO[bytes] | None = None) -> int:
    """Run the language server until the client closes the connection."""
    server = LspServer(
        stdin if stdin is not None else sys.stdin.buffer,
        stdout if stdout is not None else sys.stdout.buffer,
    )
    return server.run()
