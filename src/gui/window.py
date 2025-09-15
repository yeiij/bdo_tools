"""Main window that composes process, priority, affinity and ping sections."""

from __future__ import annotations

import queue
import threading
import platform
import sys
from pathlib import Path

from tkinter import BOTTOM, RIGHT, X, Frame, Label, StringVar, TclError, Tk, PhotoImage
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
TEXT_FOOTER = "#303030"


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

        self.text = StringVar(value="Initializing…")
        self.root.iconphoto(False, PhotoImage(file="../resources/icon.png"))
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
            fg=TEXT_FOOTER,
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

    # ----- helpers -----

    def _set_window_icon(self, process_name: str) -> None:
        """Attempt to replace the default window icon with the game's icon."""

        if platform.system().lower() != "windows":  # Only supported on Windows
            return

        exe_path = self._resolve_executable_path(process_name)
        if not exe_path:
            return

        if not self._apply_windows_icon(exe_path):
            try:
                self.root.iconbitmap(str(exe_path))
            except TclError:
                return

    def _resolve_executable_path(self, process_name: str) -> Path | None:
        """Return the absolute path to the configured executable, if available."""

        candidates = [
            Path(process_name).expanduser(),
            Path.cwd() / process_name,
            Path(__file__).resolve().parent / process_name,
        ]

        executable = Path(sys.executable) if sys.executable else None
        if executable is not None:
            try:
                candidates.append(executable.resolve().parent / process_name)
            except OSError:
                pass

        for candidate in candidates:
            try:
                if candidate.is_file():
                    return candidate.resolve()
            except OSError:
                continue

        try:
            from core.process import find_process_by_name
        except Exception:
            return None

        proc = find_process_by_name(process_name)
        if proc is None:
            return None

        try:
            exe = proc.exe()
        except Exception:
            return None

        if exe:
            path = Path(exe)
            try:
                if path.is_file():
                    return path.resolve()
            except OSError:
                return None
        return None

    def _apply_windows_icon(self, exe_path: Path) -> bool:
        """Extract and apply the icon from ``exe_path`` using the Win32 API."""

        try:
            import ctypes
            from ctypes import wintypes
        except Exception:
            return False

        shell32 = ctypes.windll.shell32
        user32 = ctypes.windll.user32

        large_icons = (wintypes.HICON * 1)()
        small_icons = (wintypes.HICON * 1)()
        extracted = shell32.ExtractIconExW(str(exe_path), 0, large_icons, small_icons, 1)
        if extracted <= 0:
            return False

        self.root.update_idletasks()
        hwnd = self.root.winfo_id()
        if not hwnd:
            return False

        WM_SETICON = 0x0080
        ICON_BIG = 1
        ICON_SMALL = 0

        if large_icons[0]:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, large_icons[0])
            user32.DestroyIcon(large_icons[0])
        if small_icons[0]:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, small_icons[0])
            user32.DestroyIcon(small_icons[0])

        return True
