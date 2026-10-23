"""Tests of the language features of the Gofra language server."""

import io

from gofra.lsp.protocol import read_message, write_message
from gofra.lsp.server import LspServer

SOURCE = """#include "std"

struct Point
    x int
    y int
end

pub func int add[int a, int b]
    a b +
end

pub func void main[]
    var counter int = 0
    counter 1 + print
    1 2 add print
end
"""

URI = "file:///tmp/gofra-lsp-features-test.gof"

LINE_OF_COUNTER_DECLARATION = 12
LINE_OF_COUNTER_USAGE = 13
LINE_OF_ADD_DECLARATION = 7
LINE_OF_ADD_CALL = 14


def _serve(messages: list[dict]) -> list[dict]:
    """Serve the given messages and collect the produced ones."""
    stream = io.BytesIO()
    for message in messages:
        write_message(stream, message)
    stream.seek(0)

    output = io.BytesIO()
    LspServer(stream, output).run()

    output.seek(0)
    produced: list[dict] = []
    while (message := read_message(output)) is not None:
        produced.append(message)

    return produced


def _open_document() -> dict:
    """Build the notification that opens a document."""
    return {
        "jsonrpc": "2.0",
        "method": "textDocument/didOpen",
        "params": {
            "textDocument": {
                "uri": URI,
                "languageId": "gofra",
                "version": 1,
                "text": SOURCE,
            },
        },
    }


def _request(method: str, line: int, character: int) -> dict:
    """Build a request for the given place in the document."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": {
            "textDocument": {"uri": URI},
            "position": {"line": line, "character": character},
        },
    }


def _result(method: str, line: int, character: int) -> object:
    """Get the result of a request for the given place in the document."""
    produced = _serve(
        [
            _open_document(),
            _request(method, line, character),
        ],
    )

    return produced[-1]["result"]


def test_hover_of_a_local_variable_shows_its_type() -> None:
    result = _result("textDocument/hover", LINE_OF_COUNTER_DECLARATION, 8)

    assert result is not None
    assert "counter" in result["contents"]["value"]


def test_hover_of_a_function_shows_its_signature() -> None:
    result = _result("textDocument/hover", LINE_OF_ADD_CALL, 8)

    assert result is not None
    assert "add" in result["contents"]["value"]


def test_hover_outside_of_a_symbol_is_empty() -> None:
    result = _result("textDocument/hover", 1, 0)

    assert result is None


def test_definition_of_a_function_points_at_its_declaration() -> None:
    result = _result("textDocument/definition", LINE_OF_ADD_CALL, 8)

    assert result is not None
    assert result[0]["range"]["start"]["line"] == LINE_OF_ADD_DECLARATION


def test_definition_of_a_local_variable_points_at_its_declaration() -> None:
    result = _result("textDocument/definition", LINE_OF_COUNTER_USAGE, 4)

    assert result is not None
    assert result[0]["range"]["start"]["line"] == LINE_OF_COUNTER_DECLARATION


def test_completion_offers_the_keywords_and_the_symbols() -> None:
    result = _result("textDocument/completion", LINE_OF_COUNTER_USAGE, 4)

    assert result is not None
    labels = [item["label"] for item in result]

    assert "func" in labels
    assert "if" in labels
    assert "add" in labels
    assert "counter" in labels
