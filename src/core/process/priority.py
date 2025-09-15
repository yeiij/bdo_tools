"""Process priority helpers."""

from __future__ import annotations

import platform
from typing import Optional

import psutil

from .utils import find_process_by_name

# Windows priority classes (values come from psutil on Windows)
_WIN_MAP = {
    psutil.IDLE_PRIORITY_CLASS: "IDLE",
    psutil.BELOW_NORMAL_PRIORITY_CLASS: "BELOW_NORMAL",
    psutil.NORMAL_PRIORITY_CLASS: "NORMAL",
    psutil.ABOVE_NORMAL_PRIORITY_CLASS: "ABOVE_NORMAL",
    psutil.HIGH_PRIORITY_CLASS: "HIGH",
    psutil.REALTIME_PRIORITY_CLASS: "REALTIME",
}


def get_priority_label(proc: psutil.Process) -> str:
    """Return a human-readable priority label for the given process."""
    try:
        nice_value = proc.nice()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "UNKNOWN"

    system = platform.system().lower()
    if system == "windows":
        return _WIN_MAP.get(nice_value, f"UNKNOWN({nice_value})")

    # On Unix, .nice() is the numeric niceness (-20..19), lower is higher priority
    try:
        niceness = int(nice_value)
    except Exception:
        return f"UNKNOWN({nice_value})"

    if niceness <= -15:
        return f"HI({niceness})"
    if niceness <= -5:
        return f"ABOVE({niceness})"
    if niceness < 5:
        return f"NORMAL({niceness})"
    if niceness < 15:
        return f"BELOW({niceness})"
    return f"LOW({niceness})"


def get_priority_by_name(process_name: str) -> Optional[str]:
    """Return the priority label for the process name, or ``None`` if not found."""
    proc = find_process_by_name(process_name)
    if not proc:
        return None
    return get_priority_label(proc)
