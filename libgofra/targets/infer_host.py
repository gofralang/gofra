from platform import system

from libgofra.targets.target import Target


def infer_host_target() -> Target | None:
    """Try to infer target from current system."""
    match system():
        case "Darwin":
            return Target.from_triplet("arm64-apple-darwin")
        case "Linux":
            return Target.from_triplet("amd64-unknown-linux")
        case "Windows":
            return Target.from_triplet("amd64-unknown-windows")
        case _:
            return None


def get_host_compliance(target: Target) -> bool:
    host_target = infer_host_target()
    if host_target is None:
        return False
    return (
        target.architecture == host_target.architecture
        and target.operating_system == host_target.operating_system
    )
