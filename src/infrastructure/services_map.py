"""Service mapping helpers."""

from __future__ import annotations

# Common BDO ports and services
_PORT_MAP = {
    8888: "Game Server (XignCode)",
    8889: "Game Server",
    8884: "Game Server",
    8885: "Game Server",
    60774: "Game Server",
    443: "Web/Auth",
    80: "HTTP",
    53: "DNS",
}

def resolve_service_name(port: int) -> str:
    """Return a human-readable service name for the given port, or 'Unknown'."""
    return _PORT_MAP.get(port, f"Unknown ({port})")


def is_game_port(port: int) -> bool:
    """Return True if the port belongs to game traffic (not web/auth)."""
    # 8888, 8889, etc are game servers. 443, 80 are usually web/auth.
    return port in (8888, 8889, 8884, 8885, 60774)
