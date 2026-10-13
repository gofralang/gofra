from collections.abc import Iterable, Sequence
from functools import lru_cache
from pathlib import Path
from shutil import which
from subprocess import DEVNULL, PIPE, run


@lru_cache(maxsize=128)
def pkgconfig_get_library_search_paths(
    library: str,
) -> list[Path] | None:
    """Get linker library search paths using `pkg-config` (e.g `--libs` yielding -l/-L flags) if it is installed in system."""
    if not which("pkg-config"):
        # `pkg-config` is not installed / misconfigured in system - cannot use that
        return None

    command = ("pkg-config", "--libs", library)
    process = run(
        command,
        check=False,
        stdout=PIPE,
        stderr=DEVNULL,
    )

    linker_flags = process.stdout.decode().split()
    return [
        Path(flag.removeprefix("-L")) for flag in linker_flags if flag.startswith("-L")
    ]


def resolve_library_search_paths(
    explicit_paths: Sequence[Path],
    libraries: Iterable[str],
    *,
    resolve_with_pkgconfig: bool,
) -> list[Path]:
    libraries_search_paths = list(explicit_paths)
    if resolve_with_pkgconfig:
        for library in libraries:
            if paths := pkgconfig_get_library_search_paths(library):
                libraries_search_paths += paths

    return libraries_search_paths
