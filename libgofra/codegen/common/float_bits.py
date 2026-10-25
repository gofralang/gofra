"""Helpers for converting between floating point values and their in-memory bit patterns."""

import struct


def float_to_bits(value: float) -> int:
    """Convert an IEEE-754 64-bit float into its raw integer bit pattern."""
    return struct.unpack("<Q", struct.pack("<d", value))[0]


def float32_to_bits(value: float) -> int:
    """Convert a 32-bit float into its raw integer bit pattern."""
    return struct.unpack("<I", struct.pack("<f", value))[0]
