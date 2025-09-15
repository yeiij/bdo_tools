"""Main window that composes process, priority, affinity and ping sections."""

from __future__ import annotations

import queue
import threading
from tkinter import BOTTOM, RIGHT, X, Frame, Label, StringVar, Tk
from tkinter import font as tkfont

from config import Settings
from gui.sections import (
    AffinitySection,
    IPResolverSection,
    LatencySection,
    PrioritySection,
    ProcessSection,
    Section,
)


WINDOW_BG = "#1F1F1F"
SURFACE_BG = "#2A2A2A"
TEXT_PRIMARY = "#F3F4F6"
TEXT_SECONDARY = "#A0A6B0"
ACCENT_BORDER = "#3B3B3B"


class AppWindow:
    """Minimal GUI that shows process status, priority, affinity and TCP latency."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        title: str = "BDO Monitor",
    ) -> None:
        self.settings = settings or Settings()

        self.root = Tk()
        self.root.title(title)
        self.root.resizable(False, False)
        self.root.configure(
            bg=WINDOW_BG,
            highlightbackground=ACCENT_BORDER,
            highlightcolor=ACCENT_BORDER,
            highlightthickness=1,
        )
        self.default_font = tkfont.Font(root=self.root, family="Segoe UI", size=10)
        self.heading_font = tkfont.Font(root=self.root, family="Segoe UI", size=14)
        self.footer_font = tkfont.Font(root=self.root, family="Segoe UI", size=10)

        self.root.option_add("*Font", self.default_font)

        # Texto principal
        self.text = StringVar(value="Initializing…")
        content = Frame(
            self.root,
            bg=SURFACE_BG,
            highlightbackground=ACCENT_BORDER,
            highlightthickness=1,
            bd=0,
        )
        content.pack(fill=X, padx=16, pady=(16, 8))
        Label(
            content,
            textvariable=self.text,
            font=self.heading_font,
            padx=16,
            pady=12,
            justify="left",
            anchor="w",
            bg=SURFACE_BG,
            fg=TEXT_PRIMARY,
        ).pack(fill=X)

        # Pie de página (abajo a la derecha)
        footer = Frame(self.root, bg=WINDOW_BG)
        footer.pack(side=BOTTOM, fill=X, padx=16, pady=(0, 12))
        Label(
            footer,
            text="By: JasonREDUX",
            font=self.footer_font,
            anchor="e",
            padx=10,
            pady=5,
            bg=WINDOW_BG,
            fg=TEXT_SECONDARY,
        ).pack(side=RIGHT)

        process_name = self.settings.process_name
        resolver_section = IPResolverSection(process_name)
        latency_section = LatencySection(resolver_section, self.settings.port)
        self.sections: list[Section] = [
            ProcessSection(process_name),
            PrioritySection(process_name),
            AffinitySection(process_name),
            resolver_section,
            latency_section,
        ]

        self._q: "queue.Queue[str]" = queue.Queue()
        self._schedule_poll()
        self._kick_worker()

    # ----- background worker -----

    def _kick_worker(self) -> None:
        threading.Thread(target=self._worker_once, daemon=True).start()

    def _worker_once(self) -> None:
        messages = [section.render() for section in self.sections]
        self._q.put("\n".join(messages))

    # ----- tkinter scheduling -----

    def _schedule_poll(self) -> None:
        try:
            while True:
                msg = self._q.get_nowait()
                self.text.set(msg)
        except queue.Empty:
            pass
        self.root.after(self.settings.poll_ms, self._schedule_poll)
        self.root.after(self.settings.refresh_ms, self._kick_worker)

    def run(self) -> None:
        self.root.mainloop()
