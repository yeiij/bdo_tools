"""Helpers to inspect remote IPs used by local processes."""

from __future__ import annotations

import ipaddress
from typing import Set

import psutil


def is_private_ip(ip: str) -> bool:
    """Return ``True`` if the IP address is private."""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def get_remote_ips_for_process(process_name: str) -> Set[str]:
    """Return remote IPs for TCP connections owned by ``process_name``."""
    ips: Set[str] = set()
    for conn in psutil.net_connections(kind="tcp"):
        try:
            if not conn.pid or not conn.raddr:
                continue
            proc = psutil.Process(conn.pid)
            if proc.name().lower() == process_name.lower():
                ips.add(conn.raddr.ip)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return ips


def get_process_ips(process_name: str, *, include_private: bool = False) -> Set[str]:
    """Return remote IPs for ``process_name``.

    Args:
        process_name: Executable name to inspect.
        include_private: When ``True`` the returned set will also contain
            private/local addresses. When ``False`` (the default) only public
            IPs are included.
    """

    ips = get_remote_ips_for_process(process_name)
    if include_private:
        return ips
    return {ip for ip in ips if not is_private_ip(ip)}


def get_public_remote_ips(process_name: str) -> Set[str]:
    """Return remote IPs for the process, excluding private addresses."""
    return get_process_ips(process_name, include_private=False)


def get_bdo_ips(process_name: str = "BlackDesert64.exe") -> Set[str]:
    """Return the set of remote IPs used by the Black Desert Online process."""
    return get_process_ips(process_name, include_private=True)
