from abc import abstractmethod


class GofraError(Exception):
    """Parent for all Gofra errors (exceptions)."""

    @abstractmethod
    def __repr__(self) -> str:
        return f"Some internal error occurred ({super().__repr__()}), that is currently not documented"
