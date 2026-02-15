"""Network infrastructure services."""

import atexit
import socket
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import psutil

from domain.models import ConnectionInfo
from domain.services import INetworkService
from infrastructure.services_map import resolve_service_name


def tcp_ping(host: str, port: int, count: int = 1, timeout: float = 1.0) -> float | None:
    """Return average latency in ms or None if failed."""
    times = []
    for _ in range(count):
        try:
            start = time.perf_counter()
            with socket.create_connection((host, port), timeout=timeout):
                duration = (time.perf_counter() - start) * 1000
                times.append(duration)
        except Exception:
            pass

    if not times:
        return None
    return statistics.mean(times)


class TcpNetworkService(INetworkService):
    def __init__(self, ping_timeout: float = 0.2, cache_ttl_s: float = 10.0, max_workers: int = 8):
        self._ping_timeout = ping_timeout
        self._cache_ttl_s = cache_ttl_s
        self._latency_cache: dict[tuple[str, int], tuple[float | None, float]] = {}
        self._inflight: set[tuple[str, int]] = set()
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="tcp-ping")
        atexit.register(self._shutdown_executor)

    def _shutdown_executor(self):
        self._executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _extract_endpoint(addr) -> tuple[str, int] | None:
        if not addr:
            return None

        if hasattr(addr, "ip") and hasattr(addr, "port"):
            return str(addr.ip), int(addr.port)

        if isinstance(addr, (tuple, list)) and len(addr) >= 2:
            return str(addr[0]), int(addr[1])

        return None

    def _get_cached_latency(self, remote_ip: str, remote_port: int) -> tuple[float | None, bool]:
        now = time.time()
        with self._lock:
            cached = self._latency_cache.get((remote_ip, remote_port))
            if not cached:
                return None, False
            latency, ts = cached
            is_stale = (now - ts) > self._cache_ttl_s
            return latency, is_stale

    def _schedule_ping(self, remote_ip: str, remote_port: int):
        key = (remote_ip, remote_port)
        with self._lock:
            if key in self._inflight:
                return
            self._inflight.add(key)
        self._executor.submit(self._ping_worker, remote_ip, remote_port)

    def _ping_worker(self, remote_ip: str, remote_port: int):
        key = (remote_ip, remote_port)
        latency = tcp_ping(remote_ip, remote_port, timeout=self._ping_timeout)
        with self._lock:
            self._latency_cache[key] = (latency, time.time())
            self._inflight.discard(key)

    def get_connections(self, pid: int) -> list[ConnectionInfo]:
        results = []
        try:
            proc = psutil.Process(pid)
            connections = proc.connections(kind="tcp")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return []

        for c in connections:
            if c.status == psutil.CONN_ESTABLISHED and c.raddr:
                remote = self._extract_endpoint(c.raddr)
                local = self._extract_endpoint(c.laddr)
                if not remote or not local:
                    continue
                remote_ip, remote_port = remote
                local_ip, local_port = local

                latency, is_stale = self._get_cached_latency(remote_ip, remote_port)
                if latency is None or is_stale:
                    self._schedule_ping(remote_ip, remote_port)

                info = ConnectionInfo(
                    pid=pid,
                    local_ip=local_ip,
                    local_port=local_port,
                    remote_ip=remote_ip,
                    remote_port=remote_port,
                    status=c.status,
                    service_name=resolve_service_name(remote_port),
                    latency_ms=latency,
                )
                results.append(info)
        return results
