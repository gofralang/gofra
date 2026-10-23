"""Tests of the language server that are done over the protocol."""

import io

from gofra.lsp.protocol import make_notification, read_message, write_message
from gofra.lsp.server import LspServer

SOURCE = """#include "std"

struct Point
    x int
    y int
end

pub func int add[int a, int b]
    a b +
end

func void main[]
    1 exit
end
"""

URI = "file:///tmp/gofra-lsp-server-test.gof"


def _frame(messages: list[dict]) -> io.BytesIO:
    """Build a stream with the given protocol messages."""
    stream = io.BytesIO()
    for message in messages:
        write_message(stream, message)
    stream.seek(0)
    return stream


def _serve(messages: list[dict]) -> list[dict]:
    """Serve the given messages and collect the produced ones."""
    output = io.BytesIO()
    LspServer(_frame(messages), output).run()

    output.seek(0)
    produced: list[dict] = []
    while (message := read_message(output)) is not None:
        produced.append(message)

    return produced


def _open_document(text: str) -> dict:
    """Build the notification that opens a document."""
    return {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": URI,
                "languageId": "gofra",
                "version": 1,
                "text": text,
            },
        },
    }


def test_initialize_reports_the_supported_capabilities() -> None:
    produced = _serve(
        [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"capabilities": {}},
            },
        ],
    )

    assert len(produced) == 1
    capabilities = produced[0]["result"]["capabilities"]
    assert capabilities["documentSymbolProvider"] is True
    assert capabilities["hoverProvider"] is True
    assert capabilities["definitionProvider"] is True


def test_opening_a_document_publishes_the_diagnostics() -> None:
    produced = _serve([_open_document(SOURCE)])

    assert len(produced) == 1
    assert produced[0]["method"] == "textDocument/publishDiagnostics"
    assert produced[0]["params"]["uri"] == URI
    assert produced[0]["params"]["diagnostics"] == []


def test_document_symbols_are_reported() -> None:
    produced = _serve(
        [
            _open_document(SOURCE),
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "textDocument/documentSymbol",
                "params": {"textDocument": {"uri": URI}},
            },
        ],
    )

    symbols = produced[-1]["result"]
    names = [symbol["name"] for symbol in symbols]

    assert "Point" in names
    assert "add" in names
    assert "main" in names


def test_unknown_method_is_reported_as_an_error() -> None:
    produced = _serve(
        [
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "textDocument/somethingElse",
                "params": {},
            },
        ],
    )

    assert produced[0]["error"]["code"] == -32601


def test_notification_for_an_unknown_method_is_ignored() -> None:
    produced = _serve([make_notification("somethingElse", {})])

    assert produced == []
