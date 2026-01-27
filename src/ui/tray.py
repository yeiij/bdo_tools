"""System tray icon management."""

import threading
from collections.abc import Callable

import pystray
from PIL import Image


class SystemTrayIcon:
    """Manages the system tray icon and its lifecycle."""

    def __init__(self, icon_path: str, on_show: Callable, on_quit: Callable):
        self.icon_path = icon_path
        self.on_show = on_show
        self.on_quit = on_quit
        self.icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None

    def run(self):
        """Start the tray icon in a separate daemon thread."""
        if self._thread and self._thread.is_alive():
            return

        try:
            image = Image.open(self.icon_path)
        except Exception:
            # Cannot proceed without a valid icon image
            return

        menu = pystray.Menu(
            pystray.MenuItem("Open GameMonitor", self._show_action, default=True),
            pystray.MenuItem("Quit", self._quit_action),
        )

        self.icon = pystray.Icon("game_monitor", image, "GameMonitor", menu)

        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop and remove the tray icon from the system tray."""
        if self.icon:
            self.icon.stop()
            self.icon = None

    def _show_action(self, icon, item):
        """Handle the 'Open' menu action."""
        self.on_show()

    def _quit_action(self, icon, item):
        """Handle the 'Quit' menu action."""
        self.on_quit()
