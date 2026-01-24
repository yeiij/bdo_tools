"""Helpers to inspect remote IPs used by local processes."""

from __future__ import annotations

import ipaddress
from typing import Dict, List, Set, NamedTuple

import psutil


class ConnectionInfo(NamedTuple):
    local_ip: str
    local_port: int
    remote_ip: str
    remote_port: int
    pid: int
    status: str


def is_private_ip(ip: str) -> bool:
    """Return ``True`` if the IP address is private."""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def get_connections_for_process(process_name: str) -> List[ConnectionInfo]:
    """Return list of TCP connections owned by ``process_name``."""
    conns: List[ConnectionInfo] = []
    for conn in psutil.net_connections(kind="tcp"):
        try:
            if conn.status != psutil.CONN_ESTABLISHED:
                continue
            if not conn.pid or not conn.raddr or not conn.laddr:
                continue
            proc = psutil.Process(conn.pid)
            if proc.name().lower() == process_name.lower():
                conns.append(
                    ConnectionInfo(
                        local_ip=conn.laddr.ip,
                        local_port=conn.laddr.port,
                        remote_ip=conn.raddr.ip,
                        remote_port=conn.raddr.port,
                        pid=conn.pid,
                        status=conn.status,
                    )
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return conns


def get_remote_ips_for_process(process_name: str) -> Set[str]:
    """Return remote IPs for TCP connections owned by ``process_name``."""
    # Wrapper for backward compatibility if needed, though we prefer using the new one.
    return {c.remote_ip for c in get_connections_for_process(process_name)}


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
