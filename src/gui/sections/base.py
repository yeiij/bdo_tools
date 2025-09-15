"""Base abstractions for GUI sections."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Section(ABC):
    """Abstract section that renders textual content for the UI."""

    @abstractmethod
    def render(self) -> str:
        """Return the textual representation of the section."""
        raise NotImplementedError
