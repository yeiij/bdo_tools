# src/gui/sections/ping.py
# Ping line builder: resolves current public game IP and measures TCP latency.

from __future__ import annotations

from typing import Set

import psutil

from scripts.ping_tcp import tcp_ping_stats


def _is_private(ip: str) -> bool:
    if ip.startswith("127.") or ip.startswith("0."):
        return True
    if ip.startswith("10.") or ip.startswith("192.168."):
        return True
    if ip.startswith("172."):
        try:
            second = int(ip.split(".")[1])
            return 16 <= second <= 31
        except Exception:
            return False
    return False


def _get_public_ips_for_process(process_name: str) -> Set[str]:
    ips: Set[str] = set()
    for conn in psutil.net_connections(kind="tcp"):
        try:
            if not conn.pid or not conn.raddr:
                continue
            if psutil.Process(conn.pid).name().lower() != process_name.lower():
                continue
            ip = conn.raddr.ip
            if not _is_private(ip):
                ips.add(ip)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return ips


def build_ping_text(process_name: str, port: int) -> str:
    """Return two lines: main ping (avg only) + details (median, p95)."""
    ips = sorted(_get_public_ips_for_process(process_name))
    if not ips:
        return "Ping: – • Open a channel in-game"

    ip = ips[0]
    stats = tcp_ping_stats(ip, port=port, count=3)
    if not stats:
        return f"Ping: {ip} • TCP failed"

    avg = stats["avg"]
    median = stats["median"]
    p95 = stats["p95"]

    line1 = f"Ping: {ip} • avg={avg:.1f} ms"
    line2 = f"Details: median={median:.1f} ms • p95={p95:.1f} ms"
    return f"{line1}\n{line2}"
