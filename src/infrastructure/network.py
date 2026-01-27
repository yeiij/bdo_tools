"""Network infrastructure services."""

import socket
import time
import statistics
import psutil
from typing import List, Optional

from domain.models import ConnectionInfo
from domain.services import INetworkService
from infrastructure.services_map import resolve_service_name


def tcp_ping(host: str, port: int, count: int = 1, timeout: float = 1.0) -> Optional[float]:
    """Return average latency in ms or None if failed."""
    times = []
    for _ in range(count):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            start = time.perf_counter()
            sock.connect((host, port))
            duration = (time.perf_counter() - start) * 1000
            times.append(duration)
            sock.close()
        except Exception:
            pass
            
    if not times:
        return None
    return statistics.mean(times)


class TcpNetworkService(INetworkService):
    def get_connections(self, pid: int) -> List[ConnectionInfo]:
        results = []
        try:
            proc = psutil.Process(pid)
            connections = proc.connections(kind='tcp')
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []

        for c in connections:
            if c.status == psutil.CONN_ESTABLISHED and c.raddr:
                remote_ip, remote_port = c.raddr
                local_ip, local_port = c.laddr
                
                # Simple synchronous ping (low timeout to prevent UI freeze)
                latency = tcp_ping(remote_ip, remote_port, timeout=0.2)
                
                info = ConnectionInfo(
                    pid=pid,
                    local_ip=local_ip,
                    local_port=local_port,
                    remote_ip=remote_ip,
                    remote_port=remote_port,
                    status=c.status,
                    service_name=resolve_service_name(remote_port),
                    latency_ms=latency
                )
                results.append(info)
        return results
