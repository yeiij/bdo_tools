# src/gui/sections/ping.py
# Ping line builder: resolves current public game IP and measures TCP latency.

from __future__ import annotations

from core.network import get_public_remote_ips, tcp_ping_stats


def build_ping_text(process_name: str, port: int) -> str:
    """Return two lines: main ping (avg only) + details (median, p95)."""
    ips = sorted(get_public_remote_ips(process_name))
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
