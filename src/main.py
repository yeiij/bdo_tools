# src/main.py
# Single entry point; launches the GUI window.

from __future__ import annotations

from config import Settings
from gui.window import AppWindow


def main() -> None:
    settings = Settings.load()
    AppWindow(settings=settings).run()


if __name__ == "__main__":
    main()
