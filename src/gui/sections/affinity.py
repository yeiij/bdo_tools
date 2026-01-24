"""Affinity section: enforce CPU affinity limits and report them."""

from __future__ import annotations

from core.process import (
    ensure_affinity_range_by_name,
    format_affinity_short,
    get_affinity_by_name,
)
from gui.sections.base import Section


class AffinitySection(Section):
    """Section that keeps the process affinity within a specific range."""

    def __init__(
        self,
        process_name: str,
        *,
        start_core: int = 2,
        end_core: int | None = None,
    ) -> None:
        self.process_name = process_name
        self.start_core = start_core
        self.end_core = end_core

    def render(self) -> str:
        """Ensure CPU affinity and return the formatted affinity string."""
        ensured = ensure_affinity_range_by_name(
            self.process_name,
            start_core=self.start_core,
            end_core=self.end_core,
        )
        affinity = get_affinity_by_name(self.process_name)
        if affinity is None:
            return "❌ Affinity: Process not running or unsupported"

        status = format_affinity_short(affinity)
        dot = "✅" if ensured else "⚠️"
        return f"{dot} Affinity: {status}"
