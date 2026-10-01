"""Entry point for toolchain CLI."""

from .main import cli_compiler_entry_point, cli_entry_point

if __name__ == "__main__":
    cli_entry_point()


__all__ = ["cli_compiler_entry_point", "cli_entry_point"]
