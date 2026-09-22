import contextlib
from pathlib import Path

_REMARK = (
    "# Internally created by Gofra toolchain\n"
    "# Do not include this newly generated build cache into git VCS"
)


def try_create_cache_gitignore(path: Path) -> bool:
    """Create .gitignore file for Git VCS to not include cache into VCS."""
    gitignore = path / ".gitignore"

    content = _REMARK + "\n*\n"

    with contextlib.suppress(PermissionError):
        gitignore.write_text(content)
        return True
    return False
