"""Main window that composes header (priority/affinity) and ping sections."""

from __future__ import annotations

import queue
import threading
from tkinter import BOTTOM, RIGHT, X, Frame, Label, StringVar, Tk

from config import Settings
from gui.sections.base import Section
from gui.sections.header import HeaderSection
from gui.sections.ping import PingSection


class AppWindow:
    """Minimal GUI that shows process priority/affinity and TCP latency."""

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

        # Texto principal
        self.text = StringVar(value="Initializing…")
        Label(
            self.root,
            textvariable=self.text,
            font=("Segoe UI", 14),
            padx=16,
            pady=12,
            justify="left",
        ).pack(fill=X)

        # Pie de página (abajo a la derecha)
        footer = Frame(self.root)
        footer.pack(side=BOTTOM, fill=X)
        Label(
            footer,
            text="By: JasonREDUX",
            font=("Segoe UI", 10),
            anchor="e",
            padx=10,
            pady=5,
        ).pack(side=RIGHT)

        self.sections: list[Section] = [
            HeaderSection(self.settings.process_name),
            PingSection(self.settings.process_name, self.settings.port),
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
