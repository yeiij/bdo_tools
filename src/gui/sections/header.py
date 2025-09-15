"""Header section: priority + affinity with a simple status dot."""

from __future__ import annotations

from gui.sections.base import Section
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


class HeaderSection(Section):
    """Section that ensures process priority/affinity and renders status."""

    def __init__(self, process_name: str) -> None:
        self.process_name = process_name

    def render(self) -> str:
        """Ensure process settings and return a one-line status summary."""
        process_name = self.process_name
        ensure_high_priority(process_name)
        ensure_affinity_range_by_name(process_name, start_core=2, end_core=None)

        prio = get_priority_by_name(process_name) or "NOT RUNNING"
        aff_str = format_affinity_short(get_affinity_by_name(process_name))
        dot = _priority_dot(prio)
        return f"{dot} {process_name} priority: {prio} • affinity: {aff_str}"
