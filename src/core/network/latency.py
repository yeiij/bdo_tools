"""Network latency helpers."""

from __future__ import annotations

import platform
import re
import socket
import statistics
import subprocess
import time
from typing import Dict, List


def tcp_ping(host: str, port: int = 443, count: int = 3, timeout: float = 2.0) -> List[float]:
    """Return a list of TCP connect times (ms) to ``host:port``."""
    times_ms: List[float] = []
    for _ in range(count):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start = time.perf_counter()
        try:
            sock.connect((host, port))
            times_ms.append((time.perf_counter() - start) * 1000.0)
        except Exception:
            # ignore timeouts/connection errors
            pass
        finally:
            sock.close()
    return times_ms


def tcp_ping_stats(
    host: str,
    port: int = 443,
    count: int = 3,
    timeout: float = 2.0,
) -> Dict[str, float]:
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


def ping_host(host: str, count: int = 5) -> float:
    """Ping a host via the system ``ping`` command and return average latency (ms)."""
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", str(count), host]
    else:
        cmd = ["ping", "-c", str(count), host]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    if system == "windows":
        match = re.search(r"Average = (\d+)ms", output)
    else:
        match = re.search(r"avg = [\d.]+/([\d.]+)/", output)

    if match:
        return float(match.group(1))
    return -1.0
