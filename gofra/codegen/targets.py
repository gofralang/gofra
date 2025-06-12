from enum import IntEnum, auto


class TargetArchitecture(IntEnum):
    ARM = auto()
    AMD = auto()


class TargetOperatingSystem(IntEnum):
    MACOS = auto()
    LINUX = auto()
