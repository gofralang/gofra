"""Helpers for converting between floating point values and their in-memory bit patterns."""

import struct


def float_to_bits(value: float) -> int:
    """Convert an IEEE-754 64-bit float into its raw integer bit pattern."""
    return struct.unpack("<Q", struct.pack("<d", value))[0]


def bits_to_float(bits: int) -> float:
    """Convert a raw 64-bit integer bit pattern into an IEEE-754 double."""
    return struct.unpack("<d", struct.pack("<Q", bits))[0]
