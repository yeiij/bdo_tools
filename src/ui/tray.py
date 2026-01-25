
import threading
import pystray
from PIL import Image
import tkinter as tk
from typing import Callable

class SystemTrayIcon:
    def __init__(self, icon_path: str, on_show: Callable, on_quit: Callable):
        self.icon_path = icon_path
        self.on_show = on_show
        self.on_quit = on_quit
        self.icon = None
        self._thread = None

    def run(self):
        """Start the tray icon in a separate thread."""
        if self._thread and self._thread.is_alive():
            return

        try:
            image = Image.open(self.icon_path)
        except Exception:
            # Fallback or error handling if icon missing
            # Proceeding without icon might fail pystray, usually better to return or warn
            return

        menu = pystray.Menu(
            pystray.MenuItem("Open BDO Monitor", self._show_action, default=True),
            pystray.MenuItem("Quit", self._quit_action)
        )

        self.icon = pystray.Icon("bdo_monitor", image, "BDO Monitor", menu)
        
        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop and remove the tray icon."""
        if self.icon:
            self.icon.stop()
            self.icon = None

    def _show_action(self, icon, item):
        self.on_show()

    def _quit_action(self, icon, item):
        self.on_quit()
