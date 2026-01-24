"""Compatibility wrapper that combines IP and latency sub-sections."""

from __future__ import annotations

from gui.sections.base import Section
from gui.sections.ip_resolver import IPResolverSection
from gui.sections.latency import LatencySection


class PingSection(Section):
    """Render the legacy ping block using the new resolver and latency sections."""

    def __init__(self, process_name: str, port: int, *, samples: int = 3) -> None:
        self.resolver = IPResolverSection(process_name)
        self.latency = LatencySection(self.resolver, port, samples=samples)

    def render(self) -> str:
        """Replicate the legacy text output using the new sections internally."""

        self.resolver.render()
        ip = self.resolver.primary_ip
        if not ip:
            return "Ping: – • Open a channel in-game"

        self.latency.render()
        stats = self.latency.last_stats
        if not stats:
            return f"Ping: {ip} • TCP failed"

        avg = stats["avg"]
        median = stats["median"]
        p95 = stats["p95"]

        line1 = f"Ping: {ip} • avg={avg:.1f} ms"
        line2 = f"Details: median={median:.1f} ms • p95={p95:.1f} ms"
        return f"{line1}\n{line2}"
