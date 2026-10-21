"""Target specifications for build process (e.g target triple but improved)."""

from .target import (
    Target,
    Triplet,
    get_all_target_triplets,
    get_target_choices,
    resolve_target_triplet,
)

__all__ = (
    "Target",
    "Triplet",
    "get_all_target_triplets",
    "get_target_choices",
    "resolve_target_triplet",
)
