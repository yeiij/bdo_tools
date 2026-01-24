"""Network latency helpers."""

from __future__ import annotations

import platform
import re
import socket
import statistics
import subprocess
import time
from typing import Dict, List, Optional


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
    if len(samples) == 1:
        p95 = samples[0]
    else:
        p95 = statistics.quantiles(samples, n=100, method="inclusive")[94]

    return {
        "samples": float(len(samples)),
        "avg": statistics.mean(samples),
        "median": statistics.median(samples),
        "p95": p95,
    }


# Common ping output patterns grouped here to make future adjustments easier.
#
# The goal is to extract the average latency reported by different flavours of
# the ``ping`` command:
#   * Unix-like systems (Linux/macOS) emit lines similar to
#     ``rtt min/avg/max/mdev = 11.2/42.0/73.0/8.5 ms``.
#   * Windows prints a summary where the "Average" label is localised (e.g.
#     ``Average``, ``Promedio``, ``Moyenne``, ``Média``).
_PING_AVERAGE_PATTERNS = (
    re.compile(
        r"=\s*(?:\d+(?:[.,]\d+)?/)(?P<avg>\d+(?:[.,]\d+)?)(?:/[0-9.,]+)*\s*ms",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:average|promedio|moyenne|mittelwert|durchschnitt|media|média)\s*=\s*(?P<avg>\d+(?:[.,]\d+)?)\s*ms",
        re.IGNORECASE,
    ),
)


def _extract_average_latency(output: str) -> Optional[float]:
    """Return the average latency contained in ``ping`` command output."""

    for pattern in _PING_AVERAGE_PATTERNS:
        match = pattern.search(output)
        if match:
            value = match.group("avg").replace(",", ".")
            try:
                return float(value)
            except ValueError:
                continue
    return None


def ping_host(host: str, count: int = 5) -> float:
    """Ping a host via the system ``ping`` command and return average latency (ms)."""
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", str(count), host]
    else:
        cmd = ["ping", "-c", str(count), host]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    average = _extract_average_latency(output)
    if average is not None:
        return average
    return -1.0
