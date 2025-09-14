# src/main.py
# Single entry point; launches the GUI window.

from __future__ import annotations

from gui.window import AppWindow


def main() -> None:
    AppWindow().run()


if __name__ == "__main__":
    main()
