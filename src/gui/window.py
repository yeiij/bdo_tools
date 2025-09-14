# src/gui/window.py
# Main window that composes header (priority/affinity) and ping sections.

from __future__ import annotations

import queue
import threading
from tkinter import Label, StringVar, Tk, Frame, BOTTOM, RIGHT, X

from gui.sections.header import build_header_text
from gui.sections.ping import build_ping_text


PROCESS_NAME = "BlackDesert64.exe"
PORT = 443
REFRESH_MS = 2000
POLL_MS = 250


class AppWindow:
    """Minimal GUI that shows process priority/affinity and TCP latency."""

    def __init__(
        self,
        title: str = "BDO Monitor",
        process_name: str = PROCESS_NAME,
        port: int = PORT,
        refresh_ms: int = REFRESH_MS,
        poll_ms: int = POLL_MS,
    ) -> None:
        self.process_name = process_name
        self.port = port
        self.refresh_ms = refresh_ms
        self.poll_ms = poll_ms

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

        self._q: "queue.Queue[str]" = queue.Queue()
        self._schedule_poll()
        self._kick_worker()

    # ----- background worker -----

    def _kick_worker(self) -> None:
        threading.Thread(target=self._worker_once, daemon=True).start()

    def _worker_once(self) -> None:
        header = build_header_text(self.process_name)
        ping_lines = build_ping_text(self.process_name, self.port)
        self._q.put(f"{header}\n{ping_lines}")

    # ----- tkinter scheduling -----

    def _schedule_poll(self) -> None:
        try:
            while True:
                msg = self._q.get_nowait()
                self.text.set(msg)
        except queue.Empty:
            pass
        self.root.after(self.poll_ms, self._schedule_poll)
        self.root.after(self.refresh_ms, self._kick_worker)

    def run(self) -> None:
        self.root.mainloop()
