"""Compatibility wrapper around the networking latency helper."""

from __future__ import annotations

from core.network.latency import ping_host as _ping_host

__all__ = ["ping_host"]


def ping_host(host: str, count: int = 5) -> float:
    """Ping ``host`` using the system command and return the average latency."""
    return _ping_host(host=host, count=count)
