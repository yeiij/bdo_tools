# src/scripts/process_priority.py
# Utilities to read a process priority in a cross-platform way.

from __future__ import annotations

from typing import Optional
import psutil
import platform


# Windows priority classes (values come from psutil on Windows)
_WIN_MAP = {
    psutil.IDLE_PRIORITY_CLASS: "IDLE",
    psutil.BELOW_NORMAL_PRIORITY_CLASS: "BELOW_NORMAL",
    psutil.NORMAL_PRIORITY_CLASS: "NORMAL",
    psutil.ABOVE_NORMAL_PRIORITY_CLASS: "ABOVE_NORMAL",
    psutil.HIGH_PRIORITY_CLASS: "HIGH",
    psutil.REALTIME_PRIORITY_CLASS: "REALTIME",
}


def _proc_by_name(name: str) -> Optional[psutil.Process]:
    """Return the first process whose name matches (case-insensitive)."""
    lname = name.lower()
    for p in psutil.process_iter(["name"]):
        try:
            if (p.info.get("name") or "").lower() == lname:
                return p
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def get_priority_label(proc: psutil.Process) -> str:
    """Return a human-readable priority label for the given process."""
    try:
        n = proc.nice()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "UNKNOWN"

    system = platform.system().lower()
    if system == "windows":
        return _WIN_MAP.get(n, f"UNKNOWN({n})")
    # On Unix, .nice() is the numeric niceness (-20..19), lower is higher priority
    # We map common ranges to labels to keep it readable.
    try:
        niceness = int(n)
    except Exception:
        return f"UNKNOWN({n})"

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
    """Return the priority label for process name, or None if not found."""
    proc = _proc_by_name(process_name)
    if not proc:
        return None
    return get_priority_label(proc)
