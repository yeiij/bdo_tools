"""Compatibility wrapper for retrieving Black Desert Online remote IPs."""

from __future__ import annotations

from typing import Set

from core.network.ip_utils import get_bdo_ips as _get_bdo_ips

__all__ = ["get_bdo_ips"]


def get_bdo_ips(process_name: str = "BlackDesert64.exe") -> Set[str]:
    """Return the set of remote IPs used by the Black Desert Online process."""
    return _get_bdo_ips(process_name=process_name)
