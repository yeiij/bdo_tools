"""Process section: report whether the target process is running."""

from __future__ import annotations

import psutil

from core.process import find_process_by_name
from gui.sections.base import Section


class ProcessSection(Section):
    """Section that reports high-level status for the configured process."""

    def __init__(self, process_name: str) -> None:
        self.process_name = process_name

    def render(self) -> str:
        """Return a status line describing whether the process is running."""
        proc = find_process_by_name(self.process_name)
        if proc is None:
            return f"❌ Process: {self.process_name} • Not running"

        try:
            pid = proc.pid
            running = proc.is_running()
            status = proc.status()
        except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.AccessDenied):
            return f"⚠️ Process: {self.process_name} • Status unavailable"

        if not running:
            return f"⚠️ Process: {self.process_name} • PID {pid} • Not running"

        status_str = str(status).replace("_", " ").title()
        return f"✅ Process: {self.process_name} • PID {pid} • {status_str}"
