"""Priority section: enforce high priority and report the current class."""

from __future__ import annotations

from core.process import ensure_high_priority, get_priority_by_name
from gui.sections.base import Section


def _priority_dot(priority: str | None) -> str:
    """Return a colored indicator according to the priority label."""
    if not priority:
        return "❌"

    p = priority.upper()
    if "REALTIME" in p or "HIGH" in p or p.startswith("HI("):
        return "✅"
    if "ABOVE" in p or "NORMAL" in p:
        return "⚠️"
    return "❌"


class PrioritySection(Section):
    """Section that ensures a high priority class for the game client."""

    def __init__(self, process_name: str) -> None:
        self.process_name = process_name

    def render(self) -> str:
        """Ensure high priority and return the textual status line."""
        ensure_high_priority(self.process_name)
        priority = get_priority_by_name(self.process_name)
        if priority is None:
            return "❌ Priority: Process not running"

        dot = _priority_dot(priority)
        return f"{dot} Priority: {priority}"
