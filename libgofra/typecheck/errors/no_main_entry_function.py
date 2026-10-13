from libgofra.exceptions import GofraError


class NoMainEntryFunctionError(GofraError):
    def __init__(self, expected_entry_name: str) -> None:
        self.expected_entry_name = expected_entry_name

    def __repr__(self) -> str:
        return f"""No entry point function `{self.expected_entry_name}` found!

Expected executable entry point function symbol defined as `{self.expected_entry_name}` but it is missing!
Please define your entry function, or compile with output format without an entry point required.

Note: `--entry-point [name]` to redefine entry point symbol name!

{self.generic_error_name}"""
