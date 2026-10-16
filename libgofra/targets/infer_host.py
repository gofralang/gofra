from platform import machine, system

from libgofra.targets.target import Target, Triplet


def infer_host_target() -> Target | None:
    """Try to infer target from current system."""
    triplet = infer_host_target_triplet()
    if not triplet:
        return None
    return Target.from_triplet(triplet)


def infer_host_target_triplet() -> Triplet | None:
    match (system(), machine().lower()):
        case ("Darwin", "arm64"):
            return "arm64-apple-darwin"
        case ("Darwin", "x86_64") | ("Darwin", "amd64"):
            return "amd64-apple-darwin"
        case ("Linux", "x86_64") | ("Linux", "amd64"):
            return "amd64-unknown-linux"
        case ("Windows", "x86_64") | ("Windows", "amd64"):
            return "amd64-unknown-windows"
        case _:
            return None
