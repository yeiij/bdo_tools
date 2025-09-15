# src/gui/sections/header.py
# Header line builder: priority + affinity with a simple status dot.

from __future__ import annotations

from core.process import (
    ensure_affinity_range_by_name,
    ensure_high_priority,
    format_affinity_short,
    get_affinity_by_name,
    get_priority_by_name,
)


def _priority_dot(priority: str) -> str:
    """Return a colored dot according to priority (symbolic)."""
    p = (priority or "").upper()
    if "REALTIME" in p or "HIGH" in p or p.startswith("HI("):
        return "✅"
    if "ABOVE" in p or "NORMAL" in p:
        return "⚠️"
    return "❌"


def build_header_text(process_name: str) -> str:
    """
    Ensure HIGH priority and enforce affinity from core 2 to last,
    then build header text with current priority and affinity.
    """
    # Elevate priority if needed
    ensure_high_priority(process_name)
    # Enforce affinity [2..last]
    ensure_affinity_range_by_name(process_name, start_core=2, end_core=None)

    prio = get_priority_by_name(process_name) or "NOT RUNNING"
    aff_str = format_affinity_short(get_affinity_by_name(process_name))
    dot = _priority_dot(prio)
    return f"{dot} {process_name} priority: {prio} • affinity: {aff_str}"
