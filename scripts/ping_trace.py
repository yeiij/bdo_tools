"""Capture and analyze ping telemetry for GameMonitor."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from domain.models import AppSettings, ConnectionInfo  # noqa: E402
from infrastructure.network import TcpNetworkService  # noqa: E402
from infrastructure.system import PsutilProcessService  # noqa: E402

LOOPBACKS = {"127.0.0.1", "::1", "localhost"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def median(values: list[float]) -> float:
    values = sorted(values)
    return values[len(values) // 2]


def classify_connections(
    connections: list[ConnectionInfo], exitlag_active: bool
) -> tuple[list[dict[str, Any]], list[float], list[float]]:
    rows: list[dict[str, Any]] = []
    direct_latencies: list[float] = []
    proxy_latencies: list[float] = []

    for c in connections:
        is_remote_local = c.remote_ip in LOOPBACKS
        is_non_web = c.remote_port not in (53, 80, 443)
        via_exitlag = exitlag_active and is_remote_local and is_non_web

        effective_remote = "ExitLag" if via_exitlag else c.remote_ip
        effective_service = "Game Server" if via_exitlag else c.service_name

        if c.latency_ms is not None and "Game Server" in effective_service:
            if effective_remote == "ExitLag":
                proxy_latencies.append(c.latency_ms)
            else:
                direct_latencies.append(c.latency_ms)

        rows.append(
            {
                "remote_ip": effective_remote,
                "remote_port": c.remote_port,
                "service_name": effective_service,
                "latency_ms": c.latency_ms,
                "via_exitlag": via_exitlag,
            }
        )

    return rows, direct_latencies, proxy_latencies


def choose_ping(
    exitlag_process_latencies: list[float],
    direct_latencies: list[float],
    proxy_latencies: list[float],
    exitlag_active: bool,
    last_ping: float | None,
) -> tuple[float | None, str]:
    if exitlag_active and exitlag_process_latencies:
        return median(exitlag_process_latencies), "exitlag_process"

    if direct_latencies:
        return median(direct_latencies), "direct"

    if proxy_latencies:
        if exitlag_active:
            filtered = [lat for lat in proxy_latencies if lat >= 5.0]
            if filtered:
                return median(filtered), "proxy_filtered"
        else:
            return median(proxy_latencies), "proxy"

    if last_ping is not None:
        return last_ping, "carry"
    return None, "none"


def capture(args: argparse.Namespace) -> int:
    settings = AppSettings.load()
    process_service = PsutilProcessService()
    network_service = TcpNetworkService()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Tracing ping for {args.duration}s, interval={args.interval}s")
    print(f"Output: {output}")

    last_ping: float | None = None
    t_end = time.time() + args.duration

    with output.open("w", encoding="utf-8") as f:
        while time.time() < t_end:
            game_pid = process_service.get_pid(settings.game_process_name)
            exitlag_pid = process_service.get_pid(settings.network_process_name)
            exitlag_active = bool(exitlag_pid)

            record: dict[str, Any] = {
                "ts": now_iso(),
                "game_pid": game_pid,
                "exitlag_pid": exitlag_pid,
                "ping_ms": None,
                "source": "none",
                "connections": [],
            }

            if game_pid:
                connections = network_service.get_connections(game_pid)
                exitlag_connections = (
                    network_service.get_connections(exitlag_pid)
                    if exitlag_pid and exitlag_pid != game_pid
                    else []
                )
                rows, direct_latencies, proxy_latencies = classify_connections(
                    connections, exitlag_active=exitlag_active
                )
                exitlag_process_latencies = [
                    c.latency_ms
                    for c in exitlag_connections
                    if c.latency_ms is not None
                    and c.remote_ip not in LOOPBACKS
                    and c.remote_port not in (53, 80, 443)
                ]
                if not exitlag_process_latencies:
                    exitlag_process_latencies = [
                        c.latency_ms
                        for c in exitlag_connections
                        if c.latency_ms is not None and c.remote_ip not in LOOPBACKS
                    ]
                ping, source = choose_ping(
                    exitlag_process_latencies,
                    direct_latencies,
                    proxy_latencies,
                    exitlag_active=exitlag_active,
                    last_ping=last_ping,
                )
                if ping is not None:
                    last_ping = ping

                record["ping_ms"] = ping
                record["source"] = source
                record["connections"] = rows

            f.write(json.dumps(record, ensure_ascii=True) + "\n")
            f.flush()

            ping_str = "--" if record["ping_ms"] is None else f"{record['ping_ms']:.1f}"
            print(
                f"{record['ts']} ping={ping_str}ms source={record['source']} "
                f"game_pid={record['game_pid']} exitlag_pid={record['exitlag_pid']} "
                f"conns={len(record['connections'])}"
            )

            time.sleep(args.interval)

    print("Done.")
    return 0


def summarize(args: argparse.Namespace) -> int:
    path = Path(args.summary)
    if not path.exists():
        print(f"File not found: {path}")
        return 1

    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    if not rows:
        print("No rows in log.")
        return 1

    pings = [r["ping_ms"] for r in rows if r.get("ping_ms") is not None]
    sources = Counter(r.get("source", "none") for r in rows)
    conns = Counter()
    for r in rows:
        for c in r.get("connections", []):
            key = f"{c.get('remote_ip')}:{c.get('remote_port')} ({c.get('service_name')})"
            conns[key] += 1

    print(f"Rows: {len(rows)}")
    print(f"Rows with ping: {len(pings)}")
    if pings:
        print(f"Ping min/median/max: {min(pings):.1f}/{statistics.median(pings):.1f}/{max(pings):.1f} ms")
    print("Sources:")
    for source, count in sources.most_common():
        print(f"  - {source}: {count}")
    print("Top connections:")
    for key, count in conns.most_common(8):
        print(f"  - {key}: {count}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture and analyze GameMonitor ping telemetry.")
    parser.add_argument("--duration", type=int, default=60, help="Capture duration in seconds.")
    parser.add_argument("--interval", type=float, default=2.0, help="Sampling interval in seconds.")
    parser.add_argument("--output", type=str, default="ping_trace.jsonl", help="Output JSONL file.")
    parser.add_argument("--summary", type=str, help="Read an existing JSONL trace and print summary.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.summary:
        return summarize(args)
    return capture(args)


if __name__ == "__main__":
    raise SystemExit(main())
