"""Low level Language Server Protocol primitives.

Implements the JSON-RPC framing used by the protocol and holds the protocol
constants that the rest of the server works with.
"""

from __future__ import annotations

import json
from typing import IO, Final

#: Header that holds the length of the message body.
CONTENT_LENGTH_HEADER: Final = "content-length"

#: Separator between the headers and the body of a message.
HEADER_SEPARATOR: Final = b"\r\n\r\n"

# Diagnostic severities.
SEVERITY_ERROR: Final = 1
SEVERITY_WARNING: Final = 2
SEVERITY_INFORMATION: Final = 3
SEVERITY_HINT: Final = 4

# Document symbol kinds.
SYMBOL_KIND_STRUCT: Final = 23
SYMBOL_KIND_CLASS: Final = 5
SYMBOL_KIND_FUNCTION: Final = 12
SYMBOL_KIND_VARIABLE: Final = 13
SYMBOL_KIND_CONSTANT: Final = 14
SYMBOL_KIND_TYPE_PARAMETER: Final = 26

# Completion item kinds.
COMPLETION_KIND_TEXT: Final = 1
COMPLETION_KIND_METHOD: Final = 2
COMPLETION_KIND_FUNCTION: Final = 3
COMPLETION_KIND_FIELD: Final = 5
COMPLETION_KIND_VARIABLE: Final = 6
COMPLETION_KIND_CLASS: Final = 7
COMPLETION_KIND_MODULE: Final = 9
COMPLETION_KIND_KEYWORD: Final = 14
COMPLETION_KIND_CONSTANT: Final = 21
COMPLETION_KIND_STRUCT: Final = 22

# Error codes used in JSON-RPC error responses.
ERROR_CODE_METHOD_NOT_FOUND: Final = -32601
ERROR_CODE_INVALID_PARAMS: Final = -32602
ERROR_CODE_INTERNAL_ERROR: Final = -32603
ERROR_CODE_REQUEST_FAILED: Final = -32803


def read_message(stream: IO[bytes]) -> dict[str, object] | None:
    """Read a single JSON-RPC message from the given binary stream.

    :returns: Decoded message or None if the stream is exhausted or broken.
    """
    headers = _read_headers(stream)
    if headers is None:
        return None

    body_length = _body_length(headers)
    if body_length is None:
        return None

    body = stream.read(body_length)
    if body is None or len(body) < body_length:
        return None

    payload = _decode_payload(body)
    if payload is None:
        return None

    return payload


def _body_length(headers: dict[str, str]) -> int | None:
    """Get the length of the body of a message from its headers."""
    try:
        body_length = int(headers[CONTENT_LENGTH_HEADER])
    except (KeyError, ValueError):
        return None

    if body_length <= 0:
        return None

    return body_length


def _decode_payload(body: bytes) -> dict[str, object] | None:
    """Decode the body of a message."""
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    return payload


def _read_headers(stream: IO[bytes]) -> dict[str, str] | None:
    """Read the headers of a message from the given binary stream."""
    headers: dict[str, str] = {}

    while True:
        raw_line = stream.readline()
        if not raw_line:
            return None

        line = raw_line.strip()
        if not line:
            return headers

        name, _, value = line.decode("ascii", errors="replace").partition(":")
        headers[name.strip().lower()] = value.strip()


def write_message(stream: IO[bytes], payload: dict[str, object]) -> None:
    """Write a single JSON-RPC message into the given binary stream."""
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    stream.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    stream.write(body)
    stream.flush()


def make_response(request_id: object, result: object) -> dict[str, object]:
    """Build a JSON-RPC response for the given request."""
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def make_error_response(
    request_id: object,
    code: int,
    message: str,
) -> dict[str, object]:
    """Build a JSON-RPC error response for the given request."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def make_notification(method: str, params: object) -> dict[str, object]:
    """Build a JSON-RPC notification with the given method and params."""
    return {"jsonrpc": "2.0", "method": method, "params": params}
