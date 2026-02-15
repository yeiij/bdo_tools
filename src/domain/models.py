"""Domain models."""

import json
import os
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ProcessStatus(Enum):
    RUNNING = auto()
    NOT_RUNNING = auto()
    UNKNOWN = auto()


@dataclass
class ConnectionInfo:
    pid: int
    local_ip: str
    local_port: int
    remote_ip: str
    remote_port: int
    status: str
    service_name: str
    latency_ms: float | None = None


@dataclass
class AppSettings:
    game_process_name: str = "BlackDesert64.exe"
    network_process_name: str = "ExitLag.exe"
    interval: int = 1000
    theme: str = "dark"
    game_target_priority: str | None = None
    game_target_affinity: list[int] | None = None
    network_target_priority: str | None = None
    network_target_affinity: list[int] | None = None
    other_targets: list[dict[str, Any]] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        """Serialize settings to the canonical on-disk schema."""
        targets: list[dict[str, Any]] = [
            {
                "process": self.game_process_name,
                "role": "game",
                "priority": self.game_target_priority,
                "affinity": self.game_target_affinity,
            },
            {
                "process": self.network_process_name,
                "role": "network",
                "priority": self.network_target_priority,
                "affinity": self.network_target_affinity,
            },
        ]

        for t in self.other_targets:
            if not isinstance(t, dict):
                continue
            process = t.get("process")
            if not isinstance(process, str) or not process:
                continue
            affinity = t.get("affinity")
            affinity = affinity if isinstance(affinity, list) else None
            targets.append(
                {
                    "process": process,
                    "role": "other",
                    "priority": t.get("priority"),
                    "affinity": affinity,
                }
            )

        return {
            "interval": self.interval,
            "theme": self.theme,
            "targets": targets,
        }

    @staticmethod
    def default_path() -> str:
        """Return the default settings path for the current platform."""
        if os.name == "nt":
            base = os.getenv("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
        else:
            base = os.getenv("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
        return os.path.join(base, "GamerMonitor", "settings.json")

    def save(self, path: str | None = None):
        """Save settings to a JSON file."""
        final_path = path or self.default_path()
        parent = os.path.dirname(final_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        raw = json.dumps(self.to_json_dict(), indent=4)
        # Keep affinity arrays in a single line for easier manual edits.
        raw = re.sub(
            r'"affinity": \[(.*?)\]',
            lambda m: '"affinity": [' + " ".join(m.group(1).replace("\n", " ").split()) + "]",
            raw,
            flags=re.DOTALL,
        )
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(raw + "\n")

    @classmethod
    def load(cls, path: str | None = None) -> AppSettings:
        """Load settings from a JSON file."""
        data = {}
        final_path = path or cls.default_path()
        if os.path.exists(final_path):
            try:
                with open(final_path, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

        if data:
            # Parse `targets` and resolve entries by role (`game`, `network`, `other`).
            targets = data.get("targets")
            if isinstance(targets, list):
                dict_targets = [t for t in targets if isinstance(t, dict)]
                game_target = next(
                    (
                        t
                        for t in dict_targets
                        if isinstance(t.get("role"), str) and t.get("role", "").strip().lower() == "game"
                    ),
                    None,
                )
                network_target = next(
                    (
                        t
                        for t in dict_targets
                        if isinstance(t.get("role"), str) and t.get("role", "").strip().lower() == "network"
                    ),
                    None,
                )

                others: list[dict[str, Any]] = []
                for t in dict_targets:
                    if t is game_target or t is network_target:
                        continue
                    process = t.get("process")
                    if not isinstance(process, str) or not process:
                        continue
                    affinity = t.get("affinity")
                    affinity = affinity if isinstance(affinity, list) else None
                    priority = t.get("priority")
                    if not isinstance(priority, str):
                        priority = None
                    others.append(
                        {
                            "process": process,
                            "role": "other",
                            "priority": priority,
                            "affinity": affinity,
                        }
                    )
                data["other_targets"] = others

                if game_target:
                    process = game_target.get("process")
                    if isinstance(process, str) and process:
                        data["game_process_name"] = process
                    priority = game_target.get("priority")
                    data["game_target_priority"] = priority if isinstance(priority, str) else None
                    affinity = game_target.get("affinity")
                    data["game_target_affinity"] = affinity if isinstance(affinity, list) else None
                if network_target:
                    process = network_target.get("process")
                    if isinstance(process, str) and process:
                        data["network_process_name"] = process
                    priority = network_target.get("priority")
                    data["network_target_priority"] = priority if isinstance(priority, str) else None
                    affinity = network_target.get("affinity")
                    data["network_target_affinity"] = affinity if isinstance(affinity, list) else None

            # Enforce minimum refresh interval (1000 ms) to avoid overly aggressive polling.
            if "interval" in data:
                data["interval"] = max(data["interval"], 1000)

            # Defensive normalization
            if not isinstance(data.get("game_process_name"), str) or not data.get("game_process_name"):
                data["game_process_name"] = cls().game_process_name
            if not isinstance(data.get("network_process_name"), str) or not data.get("network_process_name"):
                data["network_process_name"] = cls().network_process_name
            if not isinstance(data.get("game_target_affinity"), list):
                data["game_target_affinity"] = None
            if not isinstance(data.get("network_target_affinity"), list):
                data["network_target_affinity"] = None
            if not isinstance(data.get("other_targets"), list):
                data["other_targets"] = []

            # Filter keys to match dataclass fields
            valid_keys = cls.__dataclass_fields__.keys()
            filtered_data = {k: v for k, v in data.items() if k in valid_keys}
            return cls(**filtered_data)

        return cls()
