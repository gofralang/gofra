import json
import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from dataclasses import dataclass
from typing import NoReturn, get_args

from libgofra.targets import Target
from libgofra.targets.infer_host import infer_host_target_triplet
from libgofra.targets.target import Triplet


@dataclass(slots=True, frozen=True)
class TargetsArguments:
    json: bool


def parse_arguments(namespace: Namespace) -> TargetsArguments:
    return TargetsArguments(json=bool(namespace.json))


def build_parser(subparsers: "_SubParsersAction[ArgumentParser]") -> ArgumentParser:
    parser = subparsers.add_parser(
        "targets",
        help="Get available targets",
        description="List all targets supported by compiler, and their availability on host",
        allow_abbrev=False,
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Display as JSON",
        required=False,
        default=False,
    )

    return parser


def execute(args: TargetsArguments) -> NoReturn:
    """Perform targets command goal that displays all possible targets."""
    _ = args

    known_targets = sorted(
        [Target.from_triplet(triplet) for triplet in set(get_args(Triplet.__value__))],
        key=lambda t: t.triplet,
    )

    host_triplet = infer_host_target_triplet()

    if args.json:
        payload = [
            {
                "triplet": t.triplet,
                "architecture": t.architecture,
                "os": t.operating_system,
                "status": t.status,
                "is_host": t.triplet == host_triplet,
            }
            for t in known_targets
        ]
        print(json.dumps(payload, indent=2))
        return sys.exit(0)

    print(f"{'TRIPLET':30} {'STATUS':20} {'HOST'}")
    for target in known_targets:
        is_host = target.triplet == host_triplet
        print(
            f"{(target.triplet):30} {target.status:20} {'native' if is_host else '-'}",
        )

    return sys.exit(0)
