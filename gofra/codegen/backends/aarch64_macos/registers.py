from __future__ import annotations

from typing import Literal

####
# Bare AARCH64 related
####

# Stack is aligment to specified bytes count
# Each cell of an stack must be within that size
# Pushing >2 cells onto stack will lead to cell overflow due to language stack nature.
AARCH64_STACK_ALIGNMENT = 16

# Bits count (size) for different word types
AARCH64_HALF_WORD_BITS = 0xFFFF  # 4 bytes (16 bits)
AARCH64_DOUBLE_WORD_BITS = 0xFFFF_FFFF_FFFF_FFFF  # 16 bytes (64 bits)

# Registers specification for AARCH64
# Skips some of registers (X8-X15, X18-X30) due to currently being unused
# W-registers is skipped due to same unusage
type AARCH64_ABI_REGISTERS = Literal["X0", "X1", "X2", "X3", "X4", "X5", "X6", "X7"]
type AARCH64_IPC_REGISTERS = Literal["X16", "X17"]
type AARCH64_GP_REGISTERS = AARCH64_ABI_REGISTERS | AARCH64_IPC_REGISTERS
AARCH64_SP = "SP"

####
# Gofra related
####

# Temporary register used in for example pushing integer (store into register -> store onto stack)
AARCH64_GOFRA_TEMP_REGISTER: AARCH64_ABI_REGISTERS = "X7"

####
# MacOS related
####

# MacOS syscall convention
AARCH64_MACOS_SYSCALL_NUMBER_REGISTER: AARCH64_IPC_REGISTERS = "X16"
AARCH64_MACOS_SYSCALL_RETVAL_REGISTER: AARCH64_ABI_REGISTERS = "X0"
