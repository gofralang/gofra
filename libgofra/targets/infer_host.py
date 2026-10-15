from platform import system

from libgofra.targets.target import Target, Triplet


def infer_host_target() -> Target | None:
    """Try to infer target from current system."""
    triplet = infer_host_target_triplet()
    if not triplet:
        return None
    return Target.from_triplet(triplet)


def infer_host_target_triplet() -> Triplet | None:
    match system():
        case "Darwin":
            return "arm64-apple-darwin"
        case "Linux":
            return "amd64-unknown-linux"
        case "Windows":
            return "amd64-unknown-windows"
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
