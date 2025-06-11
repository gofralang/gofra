from enum import IntEnum, auto


class TargetArchitecture(IntEnum):
    ARM = auto()
    X86 = auto()


class TargetOperatingSystem(IntEnum):
    MACOS = auto()
    LINUX = auto()
