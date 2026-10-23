"""Entry point of the Gofra language server."""

from __future__ import annotations

import sys

from gofra.lsp.server import serve


def main() -> int:
    """Run the language server until the client closes the connection."""
    return serve()


if __name__ == "__main__":
    sys.exit(main())
