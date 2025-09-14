# src/scripts/ping_tcp.py
# TCP connect timing (more representative than ICMP for game traffic)

from __future__ import annotations

import socket
import statistics
import time
from typing import Dict, List, Tuple


def tcp_ping(host: str, port: int = 443, count: int = 3, timeout: float = 2.0) -> List[float]:
    """Return a list of TCP connect times (ms) to host:port."""
    times_ms: List[float] = []
    for _ in range(count):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        t0 = time.perf_counter()
        try:
            s.connect((host, port))
            times_ms.append((time.perf_counter() - t0) * 1000.0)
        except Exception:
            # ignore timeouts/connection errors
            pass
        finally:
            s.close()
    return times_ms


def tcp_ping_stats(host: str, port: int = 443, count: int = 3, timeout: float = 2.0) -> Dict[str, float]:
    """Return stats dict with avg/median/p95 (ms). Empty dict if no samples."""
    samples = tcp_ping(host, port=port, count=count, timeout=timeout)
    if not samples:
        return {}
    return {
        "samples": float(len(samples)),
        "avg": statistics.mean(samples),
        "median": statistics.median(samples),
        "p95": statistics.quantiles(samples, n=20)[-1] if len(samples) > 1 else samples[0],
    }
