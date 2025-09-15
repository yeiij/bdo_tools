"""Section that reports TCP latency metrics for a resolved IP."""

from __future__ import annotations

from collections.abc import Callable

from core.network import tcp_ping_stats
from gui.sections.base import Section
from gui.sections.ip_resolver import IPResolverSection


class LatencySection(Section):
    """Measure TCP latency against an IP obtained elsewhere."""

    def __init__(
        self,
        ip_source: Callable[[], str | None] | IPResolverSection,
        port: int,
        *,
        samples: int = 3,
    ) -> None:
        self._ip_supplier: Callable[[], str | None]
        if isinstance(ip_source, IPResolverSection):
            self._ip_supplier = ip_source.get_primary_ip
        else:
            self._ip_supplier = ip_source

        self.port = port
        self.samples = samples
        self._current_ip: str | None = None
        self._last_stats: dict[str, float] | None = None

    @property
    def current_ip(self) -> str | None:
        """Return the IP address that was probed in the last render call."""

        return self._current_ip

    @property
    def last_stats(self) -> dict[str, float] | None:
        """Return the cached latency statistics from the last render."""

        return self._last_stats

    def render(self) -> str:
        """Return latency statistics for the provided IP."""

        ip = self._ip_supplier()
        self._current_ip = ip
        if not ip:
            self._last_stats = None
            return "Latency: – • Waiting for server IP"

        stats = tcp_ping_stats(ip, port=self.port, count=self.samples)
        if not stats:
            self._last_stats = None
            return f"Latency: {ip} • TCP failed"

        self._last_stats = stats
        avg = stats["avg"]
        median = stats["median"]
        p95 = stats["p95"]

        line1 = f"Latency: {ip} • avg={avg:.1f} ms"
        line2 = f"Details: median={median:.1f} ms • p95={p95:.1f} ms"
        return f"{line1}\n{line2}"

