"""./scrips/ping_host.py"""
import platform
import subprocess
import re


def ping_host(host: str, count: int = 5) -> float:
    """Ping a host and return average latency in ms."""
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