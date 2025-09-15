"""Command line interface for BDO Tools network utilities."""

from __future__ import annotations

import argparse
from typing import Sequence

from core.network import get_process_ips, ping_host

DEFAULT_PROCESS_NAME = "BlackDesert64.exe"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Interact with BDO Tools network helpers from the terminal.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ping_parser = subparsers.add_parser(
        "ping",
        help="Measure the average latency to a host using the system ping command.",
    )
    ping_parser.add_argument("host", help="Host name or IP address to ping.")
    ping_parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=5,
        help="Number of echo requests to send (default: 5).",
    )
    ping_parser.set_defaults(func=_run_ping)

    ips_parser = subparsers.add_parser(
        "ips",
        help="List remote IPs currently used by a running process.",
    )
    ips_parser.add_argument(
        "-p",
        "--process",
        default=DEFAULT_PROCESS_NAME,
        help=(
            "Process name to inspect (default: %(default)s). Matches the "
            "executable name reported by the operating system."
        ),
    )
    ips_parser.add_argument(
        "--include-private",
        action="store_true",
        help="Include private/local IP addresses in the output.",
    )
    ips_parser.set_defaults(func=_run_ips)

    return parser


def _run_ping(args: argparse.Namespace) -> int:
    latency = ping_host(args.host, count=args.count)
    if latency < 0:
        print(f"Unable to determine ping to {args.host}.")
        return 1
    print(f"Average ping to {args.host}: {latency:.1f} ms")
    return 0


def _run_ips(args: argparse.Namespace) -> int:
    ips = sorted(
        get_process_ips(
            args.process,
            include_private=args.include_private,
        )
    )
    if not ips:
        print(f"No remote IPs found for process {args.process!r}.")
        return 1
    print("\n".join(ips))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Execute the CLI with ``argv`` (defaults to :data:`sys.argv`)."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
