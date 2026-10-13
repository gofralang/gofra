from collections.abc import Iterable, MutableSequence
from pathlib import Path
from typing import Literal, Protocol, assert_never

from libgofra.linker.apple.command_composer import compose_apple_linker_command
from libgofra.linker.gnu.command_composer import compose_gnu_linker_command
from libgofra.linker.output_format import LinkerOutputFormat
from libgofra.linker.profile import LinkerProfile
from libgofra.targets.target import Target


class LinkerCommandComposer(Protocol):
    @staticmethod
    def __call__(  # noqa: PLR0913, PLR0917
        objects: Iterable[Path],
        output: Path,
        target: Target,
        output_format: LinkerOutputFormat,
        libraries: MutableSequence[str],
        additional_flags: list[str],
        libraries_search_paths: list[Path],
        profile: LinkerProfile,
        executable_entry_point_symbol: str,
        *,
        cache_directory: Path | None = None,
        linker_executable: Path | None = ...,
    ) -> list[str]: ...


def get_linker_command_composer_backend(
    target: Target,
) -> LinkerCommandComposer:
    """Get linker command composer backend suitable for that target and current host."""
    if target.triplet == "arm64-apple-darwin":
        # Always use Apple linker on Darwin (e.g MacOS)
        return compose_apple_linker_command

    # Fallback to GNU
    return compose_gnu_linker_command


def resolve_linker_command_composer(
    backend: Literal["apple-ld", "gnu-ld"] | None,
    target: Target,
) -> LinkerCommandComposer:
    if backend is None:
        return get_linker_command_composer_backend(target)
    match backend:
        case "apple-ld":
            return compose_apple_linker_command
        case "gnu-ld":
            return compose_gnu_linker_command
        case _:
            assert_never(backend)
