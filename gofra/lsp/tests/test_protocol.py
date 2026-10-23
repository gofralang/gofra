"""Tests of the JSON-RPC framing of the language server."""

import io

from gofra.lsp.protocol import make_notification, read_message, write_message


def test_message_is_written_with_the_content_length_header() -> None:
    stream = io.BytesIO()

    write_message(stream, {"jsonrpc": "2.0", "method": "test", "params": {}})

    written = stream.getvalue().decode("utf-8")
    assert written.startswith("Content-Length: ")
    assert "\r\n\r\n" in written


def test_message_is_read_back() -> None:
    stream = io.BytesIO()

    write_message(stream, make_notification("test", {"value": 1}))

    stream.seek(0)
    message = read_message(stream)

    assert message is not None
    assert message["method"] == "test"
    assert message["params"] == {"value": 1}


def test_empty_stream_has_no_message() -> None:
    assert read_message(io.BytesIO()) is None


def test_broken_message_is_ignored() -> None:
    assert read_message(io.BytesIO(b"Content-Length: abc\r\n\r\n")) is None
    assert read_message(io.BytesIO(b"garbage\r\n\r\n{}")) is None


def test_unicode_is_transferred_as_is() -> None:
    stream = io.BytesIO()

    write_message(stream, make_notification("test", {"value": "привет 🐍"}))

    stream.seek(0)
    message = read_message(stream)

    assert message is not None
    assert message["params"] == {"value": "привет 🐍"}
