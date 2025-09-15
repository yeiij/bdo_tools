"""Process CPU affinity helpers."""

from __future__ import annotations

from typing import List, Optional, Set

import psutil

from .utils import find_process_by_name


def get_affinity(proc: psutil.Process) -> Optional[List[int]]:
    """Return list of CPU indexes for the process, or ``None`` if unsupported."""
    try:
        return sorted(proc.cpu_affinity())  # Windows/Linux
    except AttributeError:
        # Not supported on this platform (e.g., macOS)
        return None
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def get_affinity_by_name(process_name: str) -> Optional[List[int]]:
    """Return affinity list for the first process with the given name."""
    proc = find_process_by_name(process_name)
    if not proc:
        return None
    return get_affinity(proc)


def _compress_ranges(values: List[int]) -> str:
    """Compress ``[0,1,2,4,5]`` into ``"0-2,4-5"``."""
    if not values:
        return ""
    parts: List[str] = []
    start = prev = values[0]
    for value in values[1:]:
        if value == prev + 1:
            prev = value
            continue
        parts.append(f"{start}-{prev}" if start != prev else f"{start}")
        start = prev = value
    parts.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ",".join(parts)


def format_affinity_short(affinity: Optional[List[int]]) -> str:
    """Return a compact, human-friendly affinity string."""
    if affinity is None:
        return "N/A"
    total = psutil.cpu_count(logical=True) or 0
    if total and len(affinity) == total:
        return f"ALL ({total})"
    return f"{_compress_ranges(affinity)} ({len(affinity)})"


def set_affinity_range(
    proc: psutil.Process,
    start_core: int,
    end_core: Optional[int] = None,
) -> bool:
    """Set CPU affinity to cores ``[start_core..end_core]``, inclusive."""
    try:
        total = psutil.cpu_count(logical=True)
        if total is None or total <= 0:
            return False
        if end_core is None:
            end_core = total - 1
        start = max(0, start_core)
        end = min(end_core, total - 1)
        if start > end:
            return False
        mask = list(range(start, end + 1))
        proc.cpu_affinity(mask)
        return True
    except (AttributeError, psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
        return False


def ensure_affinity_range_by_name(
    process_name: str,
    start_core: int = 2,
    end_core: Optional[int] = None,
) -> bool:
    """Ensure the process has affinity ``[start_core..end_core]``."""
    proc = find_process_by_name(process_name)
    if not proc:
        return False

    total = psutil.cpu_count(logical=True)
    if total is None or total <= 0:
        return False

    if end_core is None:
        end_core = total - 1
    desired: Set[int] = set(range(max(0, start_core), min(end_core, total - 1) + 1))

    current = get_affinity(proc)
    if current is not None and set(current) == desired:
        return True

    if not set_affinity_range(proc, start_core=start_core, end_core=end_core):
        return False

    current_after = get_affinity(proc)
    return current_after is not None and set(current_after) == desired
