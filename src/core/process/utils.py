"""Shared process helper utilities."""

from __future__ import annotations

import platform
from typing import Optional

import psutil


def find_process_by_name(name: str) -> Optional[psutil.Process]:
    """Return the first process whose name matches ``name`` (case-insensitive)."""
    lname = name.lower()
    for proc in psutil.process_iter(["name"]):
        try:
            if (proc.info.get("name") or "").lower() == lname:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def ensure_high_priority(process_name: str) -> bool:
    """Ensure that the named process runs with a "high" priority class."""
    from .priority import get_priority_label  # Lazy import to avoid circular deps

    proc = find_process_by_name(process_name)
    if not proc:
        return False

    system = platform.system().lower()
    try:
        current = get_priority_label(proc)

        if system == "windows":
            if current not in ("HIGH", "REALTIME"):
                proc.nice(psutil.HIGH_PRIORITY_CLASS)
        else:
            # Unix: niceness -20..19, lower is higher prio
            niceness = proc.nice()
            if niceness > -10:  # not already "high enough"
                proc.nice(-10)

        # Check again
        current = get_priority_label(proc)
        return current in ("HIGH", "REALTIME", "HI(-10)", "HI(-20)")
    except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
        return False
