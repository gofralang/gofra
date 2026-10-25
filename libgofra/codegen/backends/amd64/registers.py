"""Consts and types related to AMD64 registers and architecture (including FFI/ABI/IPC)."""

from __future__ import annotations

from typing import Literal

####
# Bare AMD64 related
####


# Registers specification for AMD64
# Skips some of registers due to currently being unused
type AMD64_GP_REGISTERS = Literal[
    "rax",
    "eax",
    "rbx",
    "rdi",
    "edx",
    "rsi",
    "rcx",
    "rdx",
    "r10",
    "r8",
    "r9",
]

type AMD64_FP_REGISTERS = Literal[
    "xmm0",
    "xmm1",
    "xmm2",
    "xmm3",
    "xmm4",
    "xmm5",
    "xmm6",
    "xmm7",
]

type AMD64_REGISTERS = AMD64_GP_REGISTERS | AMD64_FP_REGISTERS


####
# Linux related
####

# Epilogue
AMD64_LINUX_EPILOGUE_EXIT_CODE = 0
AMD64_LINUX_EPILOGUE_EXIT_SYSCALL_NUMBER = 60
