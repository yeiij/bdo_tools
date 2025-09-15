"""Ping section: resolve IPs and show TCP latency statistics."""

from __future__ import annotations

from gui.sections.base import Section
from core.network import get_public_remote_ips, tcp_ping_stats


class PingSection(Section):
    """Section that reports TCP ping information for the game server."""

    def __init__(self, process_name: str, port: int, *, samples: int = 3) -> None:
        self.process_name = process_name
        self.port = port
        self.samples = samples

    def render(self) -> str:
        """Return two lines: main ping (avg only) + details (median, p95)."""
        ips = sorted(get_public_remote_ips(self.process_name))
        if not ips:
            return "Ping: – • Open a channel in-game"

        ip = ips[0]
        stats = tcp_ping_stats(ip, port=self.port, count=self.samples)
        if not stats:
            return f"Ping: {ip} • TCP failed"

        avg = stats["avg"]
        median = stats["median"]
        p95 = stats["p95"]

        line1 = f"Ping: {ip} • avg={avg:.1f} ms"
        line2 = f"Details: median={median:.1f} ms • p95={p95:.1f} ms"
        return f"{line1}\n{line2}"
