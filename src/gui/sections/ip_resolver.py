"""Section that resolves the remote IPs used by the game client."""

from __future__ import annotations

from typing import Tuple

from core.network import get_public_remote_ips
from gui.sections.base import Section


class IPResolverSection(Section):
    """Resolve and expose the remote IP addresses of the target process."""

    def __init__(self, process_name: str) -> None:
        self.process_name = process_name
        self._primary_ip: str | None = None
        self._ips: tuple[str, ...] = ()

    @property
    def primary_ip(self) -> str | None:
        """Return the last resolved public IP or ``None`` if unavailable."""

        return self._primary_ip

    @property
    def resolved_ips(self) -> Tuple[str, ...]:
        """Return all public IPs discovered in the last refresh cycle."""

        return self._ips

    def _resolve_ips(self) -> list[str]:
        return sorted(get_public_remote_ips(self.process_name))

    def get_primary_ip(self) -> str | None:
        """Return the most relevant IP for downstream consumers."""

        return self.primary_ip

    def render(self) -> str:
        """Return a textual summary of the resolved remote IP addresses."""

        ips = self._resolve_ips()
        self._ips = tuple(ips)
        self._primary_ip = ips[0] if ips else None

        if not ips:
            return "❌ IP – • Open a channel in-game"
        if len(ips) == 1:
            return f"✅ IP {ips[0]}"
        ip_list = ", ".join(ips)
        return f"✅ IP: {ip_list}"

